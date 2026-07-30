#!/bin/bash
# Usage : bash bootstrap.sh <url-du-depot-git> [domaine]
# A executer sur le VPS. Clone (ou met a jour) le projet dans /opt/gestion_motos,
# genere un .env avec des secrets forts si absent, puis lance l'installation complete.
set -e

REPO_URL="${1:?Usage: bash bootstrap.sh <url-du-depot-git> [domaine]}"
DOMAIN="${2:-g-moto.gsoft-bf.com}"
APP_DIR=/opt/gestion_motos

BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[1/2] Recuperation du code...${NC}"
if [ -d "$APP_DIR/.git" ]; then
  cd "$APP_DIR"
  git pull origin main
else
  mkdir -p "$APP_DIR"
  git clone "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
fi

echo -e "${BLUE}[2/2] Preparation du .env (si absent) puis installation...${NC}"
if [ ! -f .env ]; then
  cp .env.example .env
  sed -i "s#^SECRET_KEY=.*#SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')#" .env
  sed -i "s#^DB_PASSWORD=.*#DB_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')#" .env
  sed -i "s#^SUPERUSER_PASSWORD=.*#SUPERUSER_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')#" .env
  sed -i "s#^ALLOWED_HOSTS=.*#ALLOWED_HOSTS=${DOMAIN}#" .env
  sed -i "s#^CORS_ALLOWED_ORIGINS=.*#CORS_ALLOWED_ORIGINS=https://${DOMAIN}#" .env
  sed -i "s#^CSRF_TRUSTED_ORIGINS=.*#CSRF_TRUSTED_ORIGINS=https://${DOMAIN}#" .env
  sed -i "s#^DOMAIN=.*#DOMAIN=${DOMAIN}#" .env
  echo "  .env cree avec des secrets generes automatiquement."
else
  echo "  .env existe deja, conserve tel quel."
fi

chmod +x entrypoint.sh deploy/*.sh
bash deploy/setup_vps.sh
