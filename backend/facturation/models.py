from django.conf import settings
from django.db import models

from catalogue.models import ModeleCasque
from core.models import Agence
from stock.models import Moto


class Client(models.Model):
    class Segment(models.TextChoices):
        STANDARD = 'standard', 'Standard'
        VIP = 'vip', 'VIP'
        REVENDEUR = 'revendeur', 'Revendeur'

    agence = models.ForeignKey(Agence, on_delete=models.PROTECT, related_name='clients')
    nom = models.CharField(max_length=150)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    segment = models.CharField(max_length=20, choices=Segment.choices, default=Segment.STANDARD)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Facture(models.Model):
    class Statut(models.TextChoices):
        VALIDEE = 'validee', 'Validee'
        ANNULEE = 'annulee', 'Annulee'

    numero_facture = models.CharField(max_length=30, unique=True)
    agence = models.ForeignKey(Agence, on_delete=models.PROTECT, related_name='factures')
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='factures')
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.VALIDEE)
    remarque = models.TextField(blank=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='factures_creees',
    )
    date_facture = models.DateTimeField(auto_now_add=True)
    annule_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='factures_annulees',
        null=True, blank=True,
    )
    date_annulation = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date_facture']

    def __str__(self):
        return self.numero_facture

    @property
    def total(self):
        return sum((ligne.montant for ligne in self.lignes.all()), start=0)


class LigneFacture(models.Model):
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='lignes')
    moto = models.OneToOneField(
        Moto, on_delete=models.PROTECT, related_name='ligne_facture', null=True, blank=True,
    )
    modele_casque = models.ForeignKey(
        ModeleCasque, on_delete=models.PROTECT, related_name='+', null=True, blank=True,
    )
    designation = models.CharField(max_length=255, blank=True)
    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2)
    montant = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.montant = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)

    def __str__(self):
        if self.moto:
            return f"Moto {self.moto.numero_serie}"
        if self.modele_casque:
            return f"Casque {self.modele_casque.nom}"
        return self.designation or f"Ligne #{self.pk}"


class Declaration(models.Model):
    facture = models.OneToOneField(Facture, on_delete=models.CASCADE, related_name='declaration')
    numero_declaration = models.CharField(max_length=50, blank=True)
    date_declaration = models.DateField(null=True, blank=True)
    commentaire = models.TextField(blank=True)

    def __str__(self):
        return f"Declaration {self.facture.numero_facture}"


class CarteGrise(models.Model):
    facture = models.OneToOneField(Facture, on_delete=models.CASCADE, related_name='carte_grise')
    numero_dossier = models.CharField(max_length=50, blank=True)
    fichier = models.FileField(upload_to='cartes_grises/', null=True, blank=True)
    date_soumission = models.DateField(auto_now_add=True)
    date_reception = models.DateField(null=True, blank=True)
    date_retrait = models.DateTimeField(null=True, blank=True)
    retirer_nom = models.CharField(max_length=150, blank=True)
    retirer_telephone = models.CharField(max_length=30, blank=True)
    commentaire = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_soumission', '-id']

    @property
    def recue(self):
        return self.date_reception is not None

    @property
    def retiree(self):
        return self.date_retrait is not None

    def __str__(self):
        return f"Carte grise {self.facture.numero_facture}"


class EnvoiDepot(models.Model):
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='envois_depot')
    agence = models.ForeignKey(Agence, on_delete=models.PROTECT, related_name='envois_depot')
    date_envoi = models.DateTimeField(auto_now_add=True)
    commentaire = models.TextField(blank=True)
    envoye_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='envois_depot_crees',
    )

    class Meta:
        ordering = ['-date_envoi']

    def __str__(self):
        return f"Depot {self.client.nom} - {self.date_envoi:%d/%m/%Y}"


class DepotVente(models.Model):
    class Statut(models.TextChoices):
        EN_COURS = 'en_cours', 'En cours'
        RETOURNEE = 'retournee', 'Retournee'
        VENDUE = 'vendue', 'Vendue'

    envoi = models.ForeignKey(EnvoiDepot, on_delete=models.CASCADE, related_name='lignes')
    moto = models.ForeignKey(Moto, on_delete=models.PROTECT, related_name='depots')
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_COURS)
    ligne_facture = models.OneToOneField(
        LigneFacture, on_delete=models.SET_NULL, null=True, blank=True, related_name='depot_origine',
    )
    date_resolution = models.DateTimeField(null=True, blank=True)
    resolu_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='depots_resolus',
        null=True, blank=True,
    )

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"Depot {self.moto.numero_serie} ({self.statut})"


class Quittance(models.Model):
    class TypeDocument(models.TextChoices):
        QUITTANCE = 'quittance', 'Quittance'
        CMC = 'cmc', 'CMC'

    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='quittances')
    type_document = models.CharField(max_length=20, choices=TypeDocument.choices)
    numero = models.CharField(max_length=50, blank=True)
    fichier = models.FileField(upload_to='quittances/', null=True, blank=True)
    date_soumission = models.DateField(auto_now_add=True)
    date_retrait = models.DateTimeField(null=True, blank=True)
    retirer_nom = models.CharField(max_length=150, blank=True)
    retirer_telephone = models.CharField(max_length=30, blank=True)
    commentaire = models.TextField(blank=True)

    @property
    def retiree(self):
        return self.date_retrait is not None

    def __str__(self):
        return f"{self.get_type_document_display()} {self.facture.numero_facture}"
