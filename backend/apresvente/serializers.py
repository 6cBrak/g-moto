from rest_framework import serializers

from core.models import Utilisateur

from .models import Entretien, Garantie


class MotoAgenceValidationMixin:
    """Empeche un non-admin de creer un document pour une moto d'une autre agence."""

    def validate_moto(self, moto):
        user = self.context['request'].user
        if user.role != Utilisateur.Role.ADMIN and moto.agence_id != user.agence_id:
            raise serializers.ValidationError("Cette moto n'appartient pas a votre agence.")
        return moto


class GarantieSerializer(MotoAgenceValidationMixin, serializers.ModelSerializer):
    moto_numero_serie = serializers.CharField(source='moto.numero_serie', read_only=True)
    date_fin = serializers.DateField(read_only=True)
    active = serializers.BooleanField(read_only=True)
    cree_par_username = serializers.CharField(source='cree_par.username', read_only=True)

    class Meta:
        model = Garantie
        fields = [
            'id', 'moto', 'moto_numero_serie', 'date_debut', 'duree_mois',
            'date_fin', 'active', 'commentaire', 'cree_par', 'cree_par_username', 'date_creation',
        ]
        read_only_fields = ['id', 'cree_par', 'date_creation']


class EntretienSerializer(MotoAgenceValidationMixin, serializers.ModelSerializer):
    moto_numero_serie = serializers.CharField(source='moto.numero_serie', read_only=True)
    realise = serializers.BooleanField(read_only=True)
    cree_par_username = serializers.CharField(source='cree_par.username', read_only=True)

    class Meta:
        model = Entretien
        fields = [
            'id', 'moto', 'moto_numero_serie', 'type_entretien', 'date_prevue',
            'date_realisee', 'realise', 'kilometrage', 'commentaire',
            'cree_par', 'cree_par_username', 'date_creation',
        ]
        read_only_fields = ['id', 'date_realisee', 'cree_par', 'date_creation']
