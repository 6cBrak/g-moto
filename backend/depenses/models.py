from django.conf import settings
from django.db import models

from core.models import Agence


class Depense(models.Model):
    class Categorie(models.TextChoices):
        LOYER = 'loyer', 'Loyer'
        SALAIRE = 'salaire', 'Salaire'
        CARBURANT = 'carburant', 'Carburant'
        ENTRETIEN = 'entretien', 'Entretien'
        FOURNITURE = 'fourniture', 'Fourniture'
        TRANSPORT = 'transport', 'Transport'
        AUTRE = 'autre', 'Autre'

    agence = models.ForeignKey(Agence, on_delete=models.PROTECT, related_name='depenses')
    categorie = models.CharField(max_length=20, choices=Categorie.choices)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    justificatif = models.FileField(upload_to='justificatifs_depenses/', null=True, blank=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='depenses_creees',
    )
    date_depense = models.DateField()
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_depense']

    def __str__(self):
        return f"{self.get_categorie_display()} - {self.montant} ({self.agence.nom})"
