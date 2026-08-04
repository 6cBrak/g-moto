from decimal import Decimal

from rest_framework import serializers

from facturation.serializers import FactureAgenceValidationMixin

from .models import SessionCaisse, SortieCaisse, Versement
from .utils import calculer_montant_theorique


class VersementSerializer(FactureAgenceValidationMixin, serializers.ModelSerializer):
    agence_nom = serializers.CharField(source='agence.nom', read_only=True)
    facture_numero = serializers.CharField(source='facture.numero_facture', read_only=True)
    client_nom = serializers.CharField(source='facture.client.nom', read_only=True)
    cree_par_username = serializers.CharField(source='cree_par.username', read_only=True)
    annule_par_username = serializers.CharField(source='annule_par.username', read_only=True, default=None)

    class Meta:
        model = Versement
        fields = [
            'id', 'facture', 'facture_numero', 'client_nom', 'agence', 'agence_nom',
            'montant', 'mode_paiement', 'reference_transaction', 'statut',
            'cree_par', 'cree_par_username', 'date_versement',
            'annule_par_username', 'date_annulation',
        ]
        read_only_fields = ['id', 'agence', 'cree_par', 'date_versement', 'statut', 'date_annulation']

    def validate(self, attrs):
        facture = attrs.get('facture')
        montant = attrs.get('montant')
        if facture and montant is not None:
            deja_verse = sum(
                (v.montant for v in facture.versements.all() if v.statut == Versement.Statut.VALIDE),
                Decimal('0'),
            )
            if deja_verse + montant > facture.total:
                raise serializers.ValidationError(
                    {'montant': "Ce versement depasserait le montant total de la facture (deja soldee ou proche)."},
                )
        return attrs


class SortieCaisseSerializer(serializers.ModelSerializer):
    agence_nom = serializers.CharField(source='agence.nom', read_only=True)
    cree_par_username = serializers.CharField(source='cree_par.username', read_only=True)
    fournisseur_nom = serializers.CharField(source='fournisseur.nom', read_only=True, default=None)

    class Meta:
        model = SortieCaisse
        fields = [
            'id', 'agence', 'agence_nom', 'montant', 'motif', 'fournisseur', 'fournisseur_nom',
            'description', 'cree_par', 'cree_par_username', 'date_sortie',
        ]
        read_only_fields = ['id', 'cree_par', 'date_sortie']
        extra_kwargs = {'agence': {'required': False}}


class SessionCaisseSerializer(serializers.ModelSerializer):
    agence_nom = serializers.CharField(source='agence.nom', read_only=True)
    ouvert_par_username = serializers.CharField(source='ouvert_par.username', read_only=True)
    ferme_par_username = serializers.CharField(source='ferme_par.username', read_only=True, default=None)
    statut = serializers.SerializerMethodField()
    montant_theorique = serializers.SerializerMethodField()
    ecart = serializers.SerializerMethodField()

    class Meta:
        model = SessionCaisse
        fields = [
            'id', 'agence', 'agence_nom', 'date_session', 'montant_ouverture', 'montant_fermeture',
            'ouvert_par', 'ouvert_par_username', 'ferme_par', 'ferme_par_username',
            'date_ouverture', 'date_fermeture', 'commentaire', 'statut', 'montant_theorique', 'ecart',
        ]
        read_only_fields = fields

    def get_statut(self, obj):
        return 'fermee' if obj.date_fermeture else 'ouverte'

    def get_montant_theorique(self, obj):
        return str(calculer_montant_theorique(obj))

    def get_ecart(self, obj):
        if obj.montant_fermeture is None:
            return None
        return str(obj.montant_fermeture - calculer_montant_theorique(obj))
