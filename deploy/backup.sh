#!/bin/bash
set -e

# ── Config ────────────────────────────────────────────────────────────────────
APP_DIR="/opt/gestion_motos"
BACKUP_DIR="/opt/gestion_motos/backups"
KEEP_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/gestion_motos_$DATE.sql.gz"
LOG_FILE="$BACKUP_DIR/backup.log"

# ── Lecture du mot de passe depuis .env ───────────────────────────────────────
DB_PASSWORD=$(grep '^DB_PASSWORD=' "$APP_DIR/.env" | cut -d '=' -f2)
DB_NAME=$(grep '^DB_NAME=' "$APP_DIR/.env" | cut -d '=' -f2)

if [ -z "$DB_PASSWORD" ] || [ -z "$DB_NAME" ]; then
    echo "[$(date)] ERREUR : impossible de lire DB_PASSWORD ou DB_NAME depuis .env" >> "$LOG_FILE"
    exit 1
fi

# ── Creation du dossier backup ────────────────────────────────────────────────
mkdir -p "$BACKUP_DIR"

# ── Dump MySQL + compression ──────────────────────────────────────────────────
cd "$APP_DIR"

if docker compose exec -T db mysqldump \
    -u root \
    -p"$DB_PASSWORD" \
    --single-transaction \
    --routines \
    --triggers \
    "$DB_NAME" | gzip > "$BACKUP_FILE"; then

    SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
    echo "[$(date)] OK  : $BACKUP_FILE ($SIZE)" >> "$LOG_FILE"
else
    echo "[$(date)] ERREUR : mysqldump a echoue" >> "$LOG_FILE"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# ── Suppression des anciens backups ──────────────────────────────────────────
DELETED=$(find "$BACKUP_DIR" -name "gestion_motos_*.sql.gz" -mtime +$KEEP_DAYS -print -delete | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "[$(date)] Nettoyage : $DELETED fichier(s) supprime(s) (> $KEEP_DAYS jours)" >> "$LOG_FILE"
fi

# ── Envoi email avec le fichier en piece jointe ───────────────────────────────
MAIL_TO="esoftcommunication.net@gmail.com"
MAIL_FROM="alerte@esoftplus-bf.com"
MAIL_SUBJECT="[Gestion Motos] Backup du $(date '+%d/%m/%Y a %H:%M')"
FILENAME=$(basename "$BACKUP_FILE")
BOUNDARY="==GESTIONMOTOS_BACKUP_$(date +%s)=="

{
    printf "From: %s\r\n" "$MAIL_FROM"
    printf "To: %s\r\n" "$MAIL_TO"
    printf "Subject: %s\r\n" "$MAIL_SUBJECT"
    printf "MIME-Version: 1.0\r\n"
    printf "Content-Type: multipart/mixed; boundary=\"%s\"\r\n" "$BOUNDARY"
    printf "\r\n"

    # Corps texte
    printf -- "--%s\r\n" "$BOUNDARY"
    printf "Content-Type: text/plain; charset=utf-8\r\n"
    printf "\r\n"
    printf "Bonjour,\r\n\r\n"
    printf "Le backup automatique de Gestion Motos s'est effectue avec succes.\r\n\r\n"
    printf "  Base de donnees : %s\r\n" "$DB_NAME"
    printf "  Fichier         : %s\r\n" "$FILENAME"
    printf "  Taille          : %s\r\n" "$SIZE"
    printf "  Date            : %s\r\n" "$(date '+%d/%m/%Y a %H:%M')"
    printf "\r\n-- Gestion Motos Backup automatique\r\n"

    # Piece jointe (base64)
    printf -- "--%s\r\n" "$BOUNDARY"
    printf "Content-Type: application/gzip\r\n"
    printf "Content-Transfer-Encoding: base64\r\n"
    printf "Content-Disposition: attachment; filename=\"%s\"\r\n" "$FILENAME"
    printf "\r\n"
    base64 "$BACKUP_FILE"
    printf "\r\n"

    printf -- "--%s--\r\n" "$BOUNDARY"
} | msmtp --account=esoftplus -t

if [ $? -eq 0 ]; then
    echo "[$(date)] Mail : backup envoye a $MAIL_TO" >> "$LOG_FILE"
else
    echo "[$(date)] Mail : echec envoi a $MAIL_TO" >> "$LOG_FILE"
fi
