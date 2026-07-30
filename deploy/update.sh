#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "  =============================="
echo "   Gestion Motos — Mise a jour"
echo "  =============================="
echo -e "${NC}"

cd /opt/gestion_motos

echo -e "${BLUE}[1/3] Recuperation des mises a jour Git...${NC}"
git pull origin main

echo -e "${BLUE}[2/3] Rebuild et redemarrage des containers...${NC}"
docker compose up -d --build

echo -e "${BLUE}[3/3] Application des nouvelles migrations...${NC}"
sleep 10
docker compose exec django python manage.py migrate --noinput

echo ""
echo -e "${GREEN}  Mise a jour terminee ! Application disponible.${NC}"
