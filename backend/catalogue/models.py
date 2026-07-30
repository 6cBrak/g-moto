from django.db import models


class Marque(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Couleur(models.Model):
    nom = models.CharField(max_length=50, unique=True)
    code_hex = models.CharField(max_length=7, blank=True)

    class Meta:
        ordering = ['nom']

    def __str__(self):
        return self.nom


class TypeMoto(models.Model):
    marque = models.ForeignKey(Marque, on_delete=models.PROTECT, related_name='types_moto')
    nom = models.CharField(max_length=100)
    code = models.CharField(
        max_length=20, blank=True, help_text='Prefixe du numero de serie/chassis pour ce type',
    )
    cylindree = models.PositiveIntegerField(null=True, blank=True, help_text='Cylindree en cm3')
    seuil_alerte = models.PositiveIntegerField(
        default=3, help_text='Quantite minimale en stock avant declenchement d\'une alerte',
    )
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['marque__nom', 'nom']
        unique_together = ['marque', 'nom']

    def __str__(self):
        return f"{self.marque.nom} {self.nom}"


class ModeleCasque(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    taille = models.CharField(max_length=10, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Fournisseur(models.Model):
    nom = models.CharField(max_length=150, unique=True)
    contact = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['nom']

    def __str__(self):
        return self.nom
