import calendar
from datetime import date

from django.conf import settings
from django.db import models

from stock.models import Moto


def ajouter_mois(source_date, mois):
    mois_total = source_date.month - 1 + mois
    annee = source_date.year + mois_total // 12
    mois_resultat = mois_total % 12 + 1
    jour = min(source_date.day, calendar.monthrange(annee, mois_resultat)[1])
    return date(annee, mois_resultat, jour)


class Garantie(models.Model):
    moto = models.OneToOneField(Moto, on_delete=models.CASCADE, related_name='garantie')
    date_debut = models.DateField()
    duree_mois = models.PositiveIntegerField(default=12)
    commentaire = models.TextField(blank=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='garanties_creees',
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    @property
    def date_fin(self):
        return ajouter_mois(self.date_debut, self.duree_mois)

    @property
    def active(self):
        return date.today() <= self.date_fin

    def __str__(self):
        return f"Garantie {self.moto.numero_serie}"


class Entretien(models.Model):
    class TypeEntretien(models.TextChoices):
        VIDANGE = 'vidange', 'Vidange'
        REVISION_GENERALE = 'revision_generale', 'Revision generale'
        CONTROLE = 'controle', 'Controle'
        AUTRE = 'autre', 'Autre'

    moto = models.ForeignKey(Moto, on_delete=models.CASCADE, related_name='entretiens')
    type_entretien = models.CharField(max_length=30, choices=TypeEntretien.choices)
    date_prevue = models.DateField()
    date_realisee = models.DateField(null=True, blank=True)
    kilometrage = models.PositiveIntegerField(null=True, blank=True)
    commentaire = models.TextField(blank=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='entretiens_crees',
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date_prevue']

    @property
    def realise(self):
        return self.date_realisee is not None

    def __str__(self):
        return f"{self.get_type_entretien_display()} - {self.moto.numero_serie}"
