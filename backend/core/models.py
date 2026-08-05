from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class Agence(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    nom_commercial = models.CharField(
        max_length=150, blank=True, help_text="Nom affiche sur les documents imprimes (sinon le Nom est utilise).",
    )
    logo = models.ImageField(upload_to='agences_logos/', null=True, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    site_web = models.CharField(max_length=150, blank=True)
    rccm = models.CharField(max_length=50, blank=True, help_text="Numero de registre de commerce")
    nif = models.CharField(max_length=50, blank=True, help_text="Numero d'identification fiscale")
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Agence'
        verbose_name_plural = 'Agences'
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Utilisateur(AbstractUser):
    class Role(models.TextChoices):
        VENDEUR_CAISSIER = 'vendeur_caissier', 'Vendeur / Caissier'
        GERANT = 'gerant', 'Gerant'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VENDEUR_CAISSIER)
    agence = models.ForeignKey(
        Agence,
        on_delete=models.PROTECT,
        related_name='utilisateurs',
        null=True,
        blank=True,
        help_text="Agence de rattachement (optionnelle pour un admin multi-agences).",
    )

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class JournalActivite(models.Model):
    class Methode(models.TextChoices):
        CREATION = 'creation', 'Creation'
        MODIFICATION = 'modification', 'Modification'
        SUPPRESSION = 'suppression', 'Suppression'
        ACTION = 'action', 'Action'

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+',
    )
    utilisateur_username = models.CharField(max_length=150, blank=True)
    agence = models.ForeignKey(Agence, on_delete=models.SET_NULL, null=True, related_name='+')
    methode = models.CharField(max_length=20, choices=Methode.choices)
    ressource = models.CharField(max_length=100, blank=True)
    objet_id = models.CharField(max_length=50, blank=True)
    chemin = models.CharField(max_length=255)
    date_action = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_action']

    def __str__(self):
        return f"{self.utilisateur_username} - {self.methode} {self.chemin}"
