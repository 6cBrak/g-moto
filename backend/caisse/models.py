from django.conf import settings
from django.db import models

from core.models import Agence
from facturation.models import Facture


class Versement(models.Model):
    class ModePaiement(models.TextChoices):
        ESPECES = 'especes', 'Especes'
        ORANGE_MONEY = 'orange_money', 'Orange Money'
        MOOV_MONEY = 'moov_money', 'Moov Money'
        WAVE = 'wave', 'Wave'
        VIREMENT = 'virement', 'Virement bancaire'
        CHEQUE = 'cheque', 'Cheque'

    class Statut(models.TextChoices):
        VALIDE = 'valide', 'Valide'
        ANNULE = 'annule', 'Annule'

    facture = models.ForeignKey(Facture, on_delete=models.PROTECT, related_name='versements')
    agence = models.ForeignKey(Agence, on_delete=models.PROTECT, related_name='versements')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    mode_paiement = models.CharField(max_length=20, choices=ModePaiement.choices)
    reference_transaction = models.CharField(max_length=100, blank=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.VALIDE)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='versements_crees',
    )
    date_versement = models.DateTimeField(auto_now_add=True)
    annule_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='versements_annules',
        null=True, blank=True,
    )
    date_annulation = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date_versement']

    def __str__(self):
        return f"Versement {self.montant} - {self.facture.numero_facture}"


class SessionCaisse(models.Model):
    agence = models.ForeignKey(Agence, on_delete=models.PROTECT, related_name='sessions_caisse')
    date_session = models.DateField()
    montant_ouverture = models.DecimalField(max_digits=12, decimal_places=2)
    montant_fermeture = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ouvert_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sessions_caisse_ouvertes',
    )
    ferme_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sessions_caisse_fermees',
        null=True, blank=True,
    )
    date_ouverture = models.DateTimeField(auto_now_add=True)
    date_fermeture = models.DateTimeField(null=True, blank=True)
    commentaire = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_session']
        unique_together = ['agence', 'date_session']

    def __str__(self):
        return f"Caisse {self.agence.nom} - {self.date_session}"


class SortieCaisse(models.Model):
    class Motif(models.TextChoices):
        VERSEMENT_BANQUE = 'versement_banque', 'Versement en banque'
        REGLEMENT_FOURNISSEUR = 'reglement_fournisseur', 'Reglement fournisseur'
        AUTRE = 'autre', 'Autre'

    agence = models.ForeignKey(Agence, on_delete=models.PROTECT, related_name='sorties_caisse')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    motif = models.CharField(max_length=25, choices=Motif.choices, default=Motif.AUTRE)
    fournisseur = models.ForeignKey(
        'catalogue.Fournisseur', on_delete=models.PROTECT, related_name='reglements',
        null=True, blank=True,
    )
    description = models.CharField(max_length=255, blank=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sorties_caisse_creees',
    )
    date_sortie = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_sortie']

    def __str__(self):
        return f"Sortie {self.montant} - {self.agence.nom}"
