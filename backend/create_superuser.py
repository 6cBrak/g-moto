import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Utilisateur  # noqa: E402

USERNAME = os.environ.get('SUPERUSER_USERNAME', 'admin')
EMAIL = os.environ.get('SUPERUSER_EMAIL', 'admin@gestionmotos.local')
PASSWORD = os.environ.get('SUPERUSER_PASSWORD', 'ChangeMoi@2026!')

if not Utilisateur.objects.filter(username=USERNAME).exists():
    Utilisateur.objects.create_superuser(
        username=USERNAME, email=EMAIL, password=PASSWORD, role=Utilisateur.Role.ADMIN,
    )
    print(f"Superutilisateur '{USERNAME}' cree.")
else:
    print(f"Superutilisateur '{USERNAME}' existe deja, rien a faire.")
