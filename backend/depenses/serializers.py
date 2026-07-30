from rest_framework import serializers

from .models import Depense


class DepenseSerializer(serializers.ModelSerializer):
    agence_nom = serializers.CharField(source='agence.nom', read_only=True)
    cree_par_username = serializers.CharField(source='cree_par.username', read_only=True)

    class Meta:
        model = Depense
        fields = [
            'id', 'agence', 'agence_nom', 'categorie', 'montant', 'description',
            'justificatif', 'cree_par', 'cree_par_username', 'date_depense', 'date_creation',
        ]
        read_only_fields = ['id', 'cree_par', 'date_creation']
        extra_kwargs = {'agence': {'required': False}}
