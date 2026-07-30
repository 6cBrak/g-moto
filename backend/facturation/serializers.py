from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from core.models import Utilisateur
from stock.models import HistoriqueMoto, Moto

from .models import CarteGrise, Client, Declaration, DepotVente, EnvoiDepot, Facture, LigneFacture, Quittance


class FactureAgenceValidationMixin:
    """Empeche un non-admin de rattacher un document a une facture d'une autre agence."""

    def validate_facture(self, facture):
        user = self.context['request'].user
        if user.role != Utilisateur.Role.ADMIN and facture.agence_id != user.agence_id:
            raise serializers.ValidationError("Cette facture n'appartient pas a votre agence.")
        return facture


class ClientSerializer(serializers.ModelSerializer):
    agence_nom = serializers.CharField(source='agence.nom', read_only=True)

    class Meta:
        model = Client
        fields = [
            'id', 'agence', 'agence_nom', 'nom', 'telephone', 'email',
            'adresse', 'segment', 'date_creation',
        ]
        read_only_fields = ['id', 'date_creation']
        extra_kwargs = {'agence': {'required': False}}


class LigneFactureSerializer(serializers.ModelSerializer):
    moto_numero_serie = serializers.CharField(source='moto.numero_serie', read_only=True)
    moto_type_label = serializers.CharField(source='moto.type_moto.__str__', read_only=True)
    moto_couleur_nom = serializers.CharField(source='moto.couleur.nom', read_only=True)
    modele_casque_nom = serializers.CharField(source='modele_casque.nom', read_only=True)

    class Meta:
        model = LigneFacture
        fields = [
            'id', 'moto', 'moto_numero_serie', 'moto_type_label', 'moto_couleur_nom',
            'modele_casque', 'modele_casque_nom', 'designation', 'quantite', 'prix_unitaire', 'montant',
        ]
        read_only_fields = ['id', 'montant']

    def validate_moto(self, moto):
        if moto and moto.statut not in (Moto.Statut.EN_STOCK, Moto.Statut.EN_DEPOT):
            raise serializers.ValidationError("Cette moto n'est pas disponible a la vente.")
        return moto


class FactureSerializer(serializers.ModelSerializer):
    agence_nom = serializers.CharField(source='agence.nom', read_only=True)
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    cree_par_username = serializers.CharField(source='cree_par.username', read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_verse = serializers.SerializerMethodField()
    solde = serializers.SerializerMethodField()
    lignes = LigneFactureSerializer(many=True)

    class Meta:
        model = Facture
        fields = [
            'id', 'numero_facture', 'agence', 'agence_nom', 'client', 'client_nom',
            'statut', 'remarque', 'cree_par', 'cree_par_username', 'date_facture', 'total',
            'total_verse', 'solde', 'lignes',
        ]
        read_only_fields = ['id', 'numero_facture', 'cree_par', 'date_facture']
        extra_kwargs = {'agence': {'required': False}}

    def get_total_verse(self, obj):
        return str(sum((v.montant for v in obj.versements.all()), Decimal('0')))

    def get_solde(self, obj):
        total_verse = sum((v.montant for v in obj.versements.all()), Decimal('0'))
        return str(obj.total - total_verse)

    def validate(self, attrs):
        client = attrs.get('client')
        for ligne_data in attrs.get('lignes', []):
            moto = ligne_data.get('moto')
            if moto and moto.statut == Moto.Statut.EN_DEPOT:
                depot = moto.depots.filter(statut=DepotVente.Statut.EN_COURS).select_related('envoi').first()
                if not depot or depot.envoi.client_id != client.id:
                    raise serializers.ValidationError(
                        {'lignes': f"La moto {moto.numero_serie} est en depot chez un autre client."},
                    )
        return attrs

    def create(self, validated_data):
        lignes_data = validated_data.pop('lignes')
        request = self.context['request']
        facture = Facture.objects.create(**validated_data)

        for ligne_data in lignes_data:
            moto = ligne_data.get('moto')
            ligne = LigneFacture.objects.create(facture=facture, **ligne_data)
            if moto:
                depot_en_cours = moto.depots.filter(statut=DepotVente.Statut.EN_COURS).first()
                if depot_en_cours:
                    depot_en_cours.statut = DepotVente.Statut.VENDUE
                    depot_en_cours.ligne_facture = ligne
                    depot_en_cours.date_resolution = timezone.now()
                    depot_en_cours.resolu_par = request.user
                    depot_en_cours.save(update_fields=['statut', 'ligne_facture', 'date_resolution', 'resolu_par'])
                moto.statut = Moto.Statut.VENDUE
                moto.save(update_fields=['statut'])
                HistoriqueMoto.objects.create(
                    moto=moto,
                    type_evenement=HistoriqueMoto.TypeEvenement.VENTE,
                    agence_destination=moto.agence,
                    utilisateur=request.user,
                    commentaire=f"Vente via facture {facture.numero_facture}",
                )
        return facture


class DepotVenteSerializer(serializers.ModelSerializer):
    moto_numero_serie = serializers.CharField(source='moto.numero_serie', read_only=True)
    moto_type_label = serializers.CharField(source='moto.type_moto.__str__', read_only=True)
    moto_couleur_nom = serializers.CharField(source='moto.couleur.nom', read_only=True)
    resolu_par_username = serializers.CharField(source='resolu_par.username', read_only=True, default=None)

    class Meta:
        model = DepotVente
        fields = [
            'id', 'envoi', 'moto', 'moto_numero_serie', 'moto_type_label', 'moto_couleur_nom',
            'statut', 'date_resolution', 'resolu_par', 'resolu_par_username',
        ]
        read_only_fields = ['id', 'envoi', 'statut', 'date_resolution', 'resolu_par']


class EnvoiDepotSerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    agence_nom = serializers.CharField(source='agence.nom', read_only=True)
    envoye_par_username = serializers.CharField(source='envoye_par.username', read_only=True)
    lignes = DepotVenteSerializer(many=True, read_only=True)
    motos = serializers.PrimaryKeyRelatedField(queryset=Moto.objects.all(), many=True, write_only=True)

    class Meta:
        model = EnvoiDepot
        fields = [
            'id', 'client', 'client_nom', 'agence', 'agence_nom', 'date_envoi',
            'commentaire', 'envoye_par', 'envoye_par_username', 'lignes', 'motos',
        ]
        read_only_fields = ['id', 'date_envoi', 'envoye_par']
        extra_kwargs = {'agence': {'required': False}}

    def validate_motos(self, motos):
        if not motos:
            raise serializers.ValidationError("Selectionnez au moins une moto.")
        for moto in motos:
            if moto.statut != Moto.Statut.EN_STOCK:
                raise serializers.ValidationError(
                    f"La moto {moto.numero_serie} n'est pas disponible ({moto.get_statut_display()}).",
                )
        return motos

    def create(self, validated_data):
        motos = validated_data.pop('motos')
        request = self.context['request']
        envoi = EnvoiDepot.objects.create(**validated_data)
        for moto in motos:
            DepotVente.objects.create(envoi=envoi, moto=moto)
            moto.statut = Moto.Statut.EN_DEPOT
            moto.save(update_fields=['statut'])
            HistoriqueMoto.objects.create(
                moto=moto,
                type_evenement=HistoriqueMoto.TypeEvenement.DEPOT,
                agence_destination=moto.agence,
                utilisateur=request.user,
                commentaire=f"Envoye en depot chez {envoi.client.nom}",
            )
        return envoi


class DeclarationSerializer(FactureAgenceValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Declaration
        fields = ['id', 'facture', 'numero_declaration', 'date_declaration', 'commentaire']
        read_only_fields = ['id']


class CarteGriseSerializer(FactureAgenceValidationMixin, serializers.ModelSerializer):
    recue = serializers.BooleanField(read_only=True)
    retiree = serializers.BooleanField(read_only=True)

    class Meta:
        model = CarteGrise
        fields = [
            'id', 'facture', 'numero_dossier', 'fichier', 'date_soumission', 'date_reception',
            'recue', 'date_retrait', 'retirer_nom', 'retirer_telephone', 'retiree', 'commentaire',
        ]
        read_only_fields = ['id', 'date_soumission', 'date_reception', 'date_retrait', 'retirer_nom', 'retirer_telephone']


class QuittanceSerializer(FactureAgenceValidationMixin, serializers.ModelSerializer):
    retiree = serializers.BooleanField(read_only=True)

    class Meta:
        model = Quittance
        fields = [
            'id', 'facture', 'type_document', 'numero', 'fichier', 'date_soumission',
            'date_retrait', 'retirer_nom', 'retirer_telephone', 'retiree', 'commentaire',
        ]
        read_only_fields = ['id', 'date_soumission', 'date_retrait', 'retirer_nom', 'retirer_telephone']
