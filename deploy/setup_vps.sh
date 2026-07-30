#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "  ======================================================"
echo "   Gestion Motos — Installation"
echo "  ======================================================"
echo -e "${NC}"

cd /opt/gestion_motos

if [ ! -f .env ]; then
  echo -e "${RED}Aucun fichier .env trouve.${NC}"
  echo "Copiez .env.example vers .env et completez-le avant de relancer :"
  echo "  cp .env.example .env && nano .env"
  exit 1
fi

echo -e "${BLUE}[1/4] Preparation du reseau Traefik (si absent)...${NC}"
docker network create web 2>/dev/null || true

echo -e "${BLUE}[2/4] Build et demarrage des containers...${NC}"
docker compose up -d --build

echo -e "${BLUE}[3/4] Attente du demarrage de MySQL...${NC}"
sleep 20

echo -e "${BLUE}[4/4] Migrations et superutilisateur...${NC}"
docker compose exec django python manage.py migrate --noinput
docker compose exec django python create_superuser.py

source .env

echo ""
echo -e "${GREEN}"
echo "  ======================================================"
echo "   INSTALLATION TERMINEE AVEC SUCCES !"
echo "  ======================================================"
echo ""
echo "   URL de l'application : https://${DOMAIN}"
echo "   Interface admin      : https://${DOMAIN}/admin"
echo "   Login                : ${SUPERUSER_USERNAME}"
echo "   Mot de passe         : celui defini dans .env (SUPERUSER_PASSWORD)"
echo ""
echo "   Pour les mises a jour futures :"
echo "     bash /opt/gestion_motos/deploy/update.sh"
echo -e "  ======================================================${NC}"
