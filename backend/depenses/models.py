from django.conf import settings
from django.db import models

from core.models import Agence


class CategorieDepense(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'Categorie de depense'
        verbose_name_plural = 'Categories de depense'

    def __str__(self):
        return self.nom


class Depense(models.Model):
    agence = models.ForeignKey(Agence, on_delete=models.PROTECT, related_name='depenses')
    categorie = models.ForeignKey(CategorieDepense, on_delete=models.PROTECT, related_name='depenses')
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
        return f"{self.categorie.nom} - {self.montant} ({self.agence.nom})"
