from rest_framework import serializers

from .models import Couleur, Fournisseur, Marque, ModeleCasque, TypeMoto


class MarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = ['id', 'nom', 'actif']


class CouleurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Couleur
        fields = ['id', 'nom', 'code_hex']


class TypeMotoSerializer(serializers.ModelSerializer):
    marque_nom = serializers.CharField(source='marque.nom', read_only=True)

    class Meta:
        model = TypeMoto
        fields = ['id', 'marque', 'marque_nom', 'nom', 'code', 'cylindree', 'seuil_alerte', 'actif']


class ModeleCasqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleCasque
        fields = ['id', 'nom', 'taille', 'actif']


class FournisseurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fournisseur
        fields = ['id', 'nom', 'contact', 'telephone', 'adresse', 'actif']
