from django.conf import settings
from django.db import models

from catalogue.models import Couleur, Fournisseur, TypeMoto
from core.models import Agence


class Arrivage(models.Model):
    agence = models.ForeignKey(Agence, on_delete=models.PROTECT, related_name='arrivages')
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.PROTECT, related_name='arrivages')
    numero_bon = models.CharField(max_length=50, unique=True)
    date_arrivage = models.DateField()
    numero_facture = models.CharField(max_length=50, blank=True)
    montant_facture = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fichier_cmc = models.FileField(upload_to='cmc/', null=True, blank=True)
    commentaire = models.TextField(blank=True)
    en_depot = models.BooleanField(
        default=False,
        help_text="Motos recues en depot chez le fournisseur, a regler seulement une fois vendues.",
    )
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='arrivages_crees',
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_arrivage']

    def __str__(self):
        return f"Arrivage {self.numero_bon} ({self.agence.nom})"


class Moto(models.Model):
    class Statut(models.TextChoices):
        EN_STOCK = 'en_stock', 'En stock'
        VENDUE = 'vendue', 'Vendue'
        TRANSFEREE = 'transferee', 'Transferee'
        EN_DEPOT = 'en_depot', 'En depot'

    numero_serie = models.CharField(max_length=100, unique=True)
    type_moto = models.ForeignKey(TypeMoto, on_delete=models.PROTECT, related_name='motos')
    couleur = models.ForeignKey(Couleur, on_delete=models.PROTECT, related_name='motos')
    arrivage = models.ForeignKey(Arrivage, on_delete=models.PROTECT, related_name='motos')
    agence = models.ForeignKey(Agence, on_delete=models.PROTECT, related_name='motos')
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_STOCK)
    prix_achat = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    immatriculation = models.CharField(max_length=20, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return self.numero_serie


class HistoriqueMoto(models.Model):
    class TypeEvenement(models.TextChoices):
        ARRIVAGE = 'arrivage', 'Arrivage'
        VENTE = 'vente', 'Vente'
        TRANSFERT = 'transfert', 'Transfert'
        SAV = 'sav', 'SAV'
        DEPOT = 'depot', 'Envoi en depot'
        RETOUR_DEPOT = 'retour_depot', 'Retour de depot'

    moto = models.ForeignKey(Moto, on_delete=models.CASCADE, related_name='historique')
    type_evenement = models.CharField(max_length=20, choices=TypeEvenement.choices)
    agence_source = models.ForeignKey(
        Agence, on_delete=models.PROTECT, related_name='+', null=True, blank=True,
    )
    agence_destination = models.ForeignKey(
        Agence, on_delete=models.PROTECT, related_name='+', null=True, blank=True,
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+',
    )
    commentaire = models.TextField(blank=True)
    date_evenement = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_evenement']
        verbose_name = 'Evenement historique moto'
        verbose_name_plural = 'Historique motos'

    def __str__(self):
        return f"{self.moto.numero_serie} - {self.get_type_evenement_display()}"
