from rest_framework import serializers

from .models import CategorieDepense, Depense


class CategorieDepenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategorieDepense
        fields = ['id', 'nom', 'actif']


class DepenseSerializer(serializers.ModelSerializer):
    agence_nom = serializers.CharField(source='agence.nom', read_only=True)
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    cree_par_username = serializers.CharField(source='cree_par.username', read_only=True)

    class Meta:
        model = Depense
        fields = [
            'id', 'agence', 'agence_nom', 'categorie', 'categorie_nom', 'montant', 'description',
            'justificatif', 'cree_par', 'cree_par_username', 'date_depense', 'date_creation',
        ]
        read_only_fields = ['id', 'cree_par', 'date_creation']
        extra_kwargs = {'agence': {'required': False}}
