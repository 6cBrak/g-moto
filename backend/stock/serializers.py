from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from core.models import Agence

from .models import Arrivage, HistoriqueMoto, Moto


class ArrivageSerializer(serializers.ModelSerializer):
    agence_nom = serializers.CharField(source='agence.nom', read_only=True)
    fournisseur_nom = serializers.CharField(source='fournisseur.nom', read_only=True)
    cree_par_username = serializers.CharField(source='cree_par.username', read_only=True)
    nb_motos = serializers.IntegerField(source='motos.count', read_only=True)
    montant_facture = serializers.SerializerMethodField()

    class Meta:
        model = Arrivage
        fields = [
            'id', 'agence', 'agence_nom', 'fournisseur', 'fournisseur_nom',
            'numero_bon', 'date_arrivage', 'numero_facture', 'montant_facture',
            'commentaire', 'cree_par', 'cree_par_username', 'date_creation', 'nb_motos',
        ]
        read_only_fields = ['id', 'cree_par', 'date_creation']

    def get_montant_facture(self, obj):
        total = obj.motos.aggregate(total=Sum('prix_achat'))['total'] or Decimal('0')
        return str(total)


class MotoSerializer(serializers.ModelSerializer):
    type_moto_label = serializers.CharField(source='type_moto.__str__', read_only=True)
    couleur_nom = serializers.CharField(source='couleur.nom', read_only=True)
    agence_nom = serializers.CharField(source='agence.nom', read_only=True)
    arrivage_numero_bon = serializers.CharField(source='arrivage.numero_bon', read_only=True)
    depot_client_id = serializers.SerializerMethodField()
    depot_client_nom = serializers.SerializerMethodField()

    class Meta:
        model = Moto
        fields = [
            'id', 'numero_serie', 'type_moto', 'type_moto_label', 'couleur', 'couleur_nom',
            'arrivage', 'arrivage_numero_bon', 'agence', 'agence_nom', 'statut', 'prix_achat',
            'immatriculation', 'date_creation', 'depot_client_id', 'depot_client_nom',
        ]
        read_only_fields = ['id', 'statut', 'date_creation']
        extra_kwargs = {'agence': {'required': False}}

    def _depot_en_cours(self, obj):
        depot = getattr(obj, '_depot_en_cours_cache', None)
        if depot is None:
            depot = obj.depots.filter(statut='en_cours').select_related('envoi__client').first() or False
            obj._depot_en_cours_cache = depot
        return depot or None

    def get_depot_client_id(self, obj):
        depot = self._depot_en_cours(obj)
        return depot.envoi.client_id if depot else None

    def get_depot_client_nom(self, obj):
        depot = self._depot_en_cours(obj)
        return depot.envoi.client.nom if depot else None


class HistoriqueMotoSerializer(serializers.ModelSerializer):
    agence_source_nom = serializers.CharField(source='agence_source.nom', read_only=True)
    agence_destination_nom = serializers.CharField(source='agence_destination.nom', read_only=True)
    utilisateur_username = serializers.CharField(source='utilisateur.username', read_only=True)

    class Meta:
        model = HistoriqueMoto
        fields = [
            'id', 'moto', 'type_evenement', 'agence_source', 'agence_source_nom',
            'agence_destination', 'agence_destination_nom', 'utilisateur',
            'utilisateur_username', 'commentaire', 'date_evenement',
        ]
        read_only_fields = fields


class TransfertSerializer(serializers.Serializer):
    agence_destination = serializers.PrimaryKeyRelatedField(queryset=Agence.objects.all())
    commentaire = serializers.CharField(required=False, allow_blank=True, default='')
