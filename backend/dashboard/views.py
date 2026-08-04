from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce, TruncDay, TruncMonth
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apresvente.models import Entretien, Garantie
from caisse.models import SortieCaisse, Versement
from core.models import Agence
from core.permissions import IsAdmin
from core.utils import (
    appliquer_periode, calculer_clients_debiteurs, calculer_fournisseurs_dus, resolve_agence_filter,
)
from depenses.models import Depense
from facturation.models import CarteGrise, Facture, LigneFacture
from stock.models import Arrivage, Moto


def normaliser_periode(valeur):
    return valeur.date() if isinstance(valeur, datetime) else valeur


def calculer_tresorerie(agence_id=None):
    """Argent physiquement disponible en caisse : encaisse - depenses - sorties de caisse."""
    versements = Versement.objects.all()
    depenses = Depense.objects.all()
    sorties = SortieCaisse.objects.all()
    if agence_id:
        versements = versements.filter(agence_id=agence_id)
        depenses = depenses.filter(agence_id=agence_id)
        sorties = sorties.filter(agence_id=agence_id)
    total_encaisse = versements.aggregate(total=Sum('montant'))['total'] or 0
    total_decaisse = depenses.aggregate(total=Sum('montant'))['total'] or 0
    total_sorties = sorties.aggregate(total=Sum('montant'))['total'] or 0
    return total_encaisse - total_decaisse - total_sorties


def compter_alertes_stock(agence_id=None):
    en_stock = Moto.objects.filter(statut=Moto.Statut.EN_STOCK)
    if agence_id:
        en_stock = en_stock.filter(agence_id=agence_id)
    en_stock_counts = {
        (row['agence_id'], row['type_moto_id']): row['quantite']
        for row in en_stock.values('agence_id', 'type_moto_id').annotate(quantite=Count('id'))
    }
    combos = Moto.objects.values('agence_id', 'type_moto_id', 'type_moto__seuil_alerte').distinct()
    if agence_id:
        combos = combos.filter(agence_id=agence_id)

    return sum(
        1
        for combo in combos
        if en_stock_counts.get((combo['agence_id'], combo['type_moto_id']), 0) < (combo['type_moto__seuil_alerte'] or 0)
    )


def compter_garanties_expirant_bientot(agence_id=None, jours=30):
    aujourdhui = date.today()
    limite = aujourdhui + timedelta(days=jours)
    garanties = Garantie.objects.select_related('moto')
    if agence_id:
        garanties = garanties.filter(moto__agence_id=agence_id)
    return sum(1 for g in garanties if aujourdhui <= g.date_fin <= limite)


def compter_entretiens_a_venir(agence_id=None, jours=30):
    limite = date.today() + timedelta(days=jours)
    entretiens = Entretien.objects.filter(date_realisee__isnull=True, date_prevue__lte=limite)
    if agence_id:
        entretiens = entretiens.filter(moto__agence_id=agence_id)
    return entretiens.count()


class DashboardKPIsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agence_id = resolve_agence_filter(request)
        aujourdhui = date.today()
        premier_jour_mois = aujourdhui.replace(day=1)

        ventes_jour = Facture.objects.filter(statut=Facture.Statut.VALIDEE, date_facture__date=aujourdhui)
        if agence_id:
            ventes_jour = ventes_jour.filter(agence_id=agence_id)
        total_ventes_jour = LigneFacture.objects.filter(
            facture__in=ventes_jour,
        ).aggregate(total=Sum('montant'))['total'] or 0

        ventes_mois = Facture.objects.filter(statut=Facture.Statut.VALIDEE, date_facture__date__gte=premier_jour_mois)
        depenses_mois = Depense.objects.filter(date_depense__gte=premier_jour_mois)
        sorties_mois = SortieCaisse.objects.filter(date_sortie__date__gte=premier_jour_mois)
        if agence_id:
            ventes_mois = ventes_mois.filter(agence_id=agence_id)
            depenses_mois = depenses_mois.filter(agence_id=agence_id)
            sorties_mois = sorties_mois.filter(agence_id=agence_id)
        nb_factures_mois = ventes_mois.count()
        total_ventes_mois = LigneFacture.objects.filter(
            facture__in=ventes_mois,
        ).aggregate(total=Sum('montant'))['total'] or 0
        total_depenses_mois = depenses_mois.aggregate(total=Sum('montant'))['total'] or 0
        total_sorties_mois = sorties_mois.aggregate(total=Sum('montant'))['total'] or 0
        total_achats_mois = LigneFacture.objects.filter(
            facture__in=ventes_mois, moto__isnull=False,
        ).aggregate(total=Sum('moto__prix_achat'))['total'] or 0
        panier_moyen = (total_ventes_mois / nb_factures_mois) if nb_factures_mois else 0

        stock_total = Moto.objects.filter(statut=Moto.Statut.EN_STOCK)
        if agence_id:
            stock_total = stock_total.filter(agence_id=agence_id)
        valeur_stock = stock_total.aggregate(total=Sum('prix_achat'))['total'] or 0
        seuil_dormant = aujourdhui - timedelta(days=60)
        stock_dormant = stock_total.filter(date_creation__date__lte=seuil_dormant).count()

        debiteurs = calculer_clients_debiteurs(agence_id)
        total_reste_a_payer = sum((d['solde'] for d in debiteurs), Decimal('0'))

        fournisseurs_dus = calculer_fournisseurs_dus(agence_id)
        total_du_fournisseurs = sum((f['reste_a_payer'] for f in fournisseurs_dus), Decimal('0'))

        versements = Versement.objects.all()
        if agence_id:
            versements = versements.filter(agence_id=agence_id)
        total_encaissements = versements.aggregate(total=Sum('montant'))['total'] or 0

        total_facture_global = LigneFacture.objects.filter(facture__statut=Facture.Statut.VALIDEE)
        if agence_id:
            total_facture_global = total_facture_global.filter(facture__agence_id=agence_id)
        total_facture_global = total_facture_global.aggregate(total=Sum('montant'))['total'] or 0
        taux_recouvrement = (
            round(total_encaissements / total_facture_global * 100, 1) if total_facture_global else None
        )

        cartes_grises = CarteGrise.objects.filter(ligne_facture__facture__statut=Facture.Statut.VALIDEE)
        if agence_id:
            cartes_grises = cartes_grises.filter(ligne_facture__facture__agence_id=agence_id)
        plaques_produites = cartes_grises.filter(date_reception__isnull=False).count()
        plaques_retirees = cartes_grises.filter(date_retrait__isnull=False).count()
        plaques_a_retirer = cartes_grises.filter(date_reception__isnull=False, date_retrait__isnull=True).count()

        return Response({
            'ventes_du_jour': {
                'nb_factures': ventes_jour.count(),
                'total': str(total_ventes_jour),
            },
            'ventes_du_mois': {
                'nb_factures': ventes_mois.count(),
                'total': str(total_ventes_mois),
            },
            'depenses_du_mois': str(total_depenses_mois),
            'sorties_du_mois': str(total_sorties_mois),
            'marge_du_mois': str(total_ventes_mois - total_achats_mois),
            'panier_moyen': str(panier_moyen),
            'stock_critique': compter_alertes_stock(agence_id),
            'stock_total': stock_total.count(),
            'stock_dormant': stock_dormant,
            'valeur_stock': str(valeur_stock),
            'tresorerie': str(calculer_tresorerie(agence_id)),
            'total_encaissements': str(total_encaissements),
            'taux_recouvrement': taux_recouvrement,
            'reste_a_payer': {
                'total': str(total_reste_a_payer),
                'nb_clients': len(debiteurs),
            },
            'du_fournisseurs': {
                'total': str(total_du_fournisseurs),
                'nb_fournisseurs': sum(1 for f in fournisseurs_dus if f['reste_a_payer'] > 0),
            },
            'garanties_expirant_bientot': compter_garanties_expirant_bientot(agence_id),
            'entretiens_a_venir': compter_entretiens_a_venir(agence_id),
            'plaques_produites': plaques_produites,
            'plaques_retirees': plaques_retirees,
            'plaques_a_retirer': plaques_a_retirer,
        })


class RapportComparatifPeriodeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agence_id = resolve_agence_filter(request)
        granularite = request.query_params.get('granularite', 'mois')
        trunc = TruncMonth if granularite == 'mois' else TruncDay

        factures = Facture.objects.filter(statut=Facture.Statut.VALIDEE)
        depenses = Depense.objects.all()
        if agence_id:
            factures = factures.filter(agence_id=agence_id)
            depenses = depenses.filter(agence_id=agence_id)
        factures = appliquer_periode(factures, 'date_facture__date', request)
        depenses = appliquer_periode(depenses, 'date_depense', request)

        ventes_par_periode = {
            normaliser_periode(row['periode']): row['total']
            for row in (
                LigneFacture.objects.filter(facture__in=factures)
                .annotate(periode=trunc('facture__date_facture'))
                .values('periode')
                .annotate(total=Sum('montant'))
            )
        }
        depenses_par_periode = {
            normaliser_periode(row['periode']): row['total']
            for row in (
                depenses.annotate(periode=trunc('date_depense'))
                .values('periode')
                .annotate(total=Sum('montant'))
            )
        }

        periodes = sorted(set(ventes_par_periode) | set(depenses_par_periode))
        return Response([
            {
                'periode': periode.isoformat(),
                'total_ventes': str(ventes_par_periode.get(periode, 0)),
                'total_depenses': str(depenses_par_periode.get(periode, 0)),
            }
            for periode in periodes
        ])


class RapportComparatifAgencesView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        factures = Facture.objects.filter(statut=Facture.Statut.VALIDEE)
        factures = appliquer_periode(factures, 'date_facture__date', request)

        resultats = []
        for agence in Agence.objects.all():
            factures_agence = factures.filter(agence=agence)
            total_ventes = LigneFacture.objects.filter(
                facture__in=factures_agence,
            ).aggregate(total=Sum('montant'))['total'] or 0
            depenses_agence = appliquer_periode(Depense.objects.filter(agence=agence), 'date_depense', request)
            total_depenses = depenses_agence.aggregate(total=Sum('montant'))['total'] or 0

            resultats.append({
                'agence_id': agence.id,
                'agence': agence.nom,
                'nb_factures': factures_agence.count(),
                'total_ventes': str(total_ventes),
                'total_depenses': str(total_depenses),
                'tresorerie': str(calculer_tresorerie(agence.id)),
            })
        return Response(resultats)


class RapportMargeArrivagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agence_id = resolve_agence_filter(request)
        decimal_zero = DecimalField(max_digits=12, decimal_places=2)

        arrivages = Arrivage.objects.select_related('agence', 'fournisseur')
        if agence_id:
            arrivages = arrivages.filter(agence_id=agence_id)
        q = request.query_params.get('q')
        if q:
            arrivages = arrivages.filter(Q(numero_bon__icontains=q) | Q(fournisseur__nom__icontains=q))
        arrivages = appliquer_periode(arrivages, 'date_arrivage', request)

        # Sous-requete plutot qu'une jointure directe : un moto peut avoir plusieurs
        # LigneFacture au fil du temps (vente annulee puis revendue), donc joindre
        # motos->lignes_facture dans la meme annotate() ferait un fan-out qui
        # doublerait aussi total_revient (Sum('motos__prix_achat')).
        total_vente_subquery = LigneFacture.objects.filter(
            moto__arrivage_id=OuterRef('pk'), facture__statut=Facture.Statut.VALIDEE,
        ).values('moto__arrivage_id').annotate(total=Sum('montant')).values('total')

        arrivages = arrivages.annotate(
            nb_motos=Count('motos', distinct=True),
            total_revient=Coalesce(Sum('motos__prix_achat'), 0, output_field=decimal_zero),
            total_vente=Coalesce(Subquery(total_vente_subquery, output_field=decimal_zero), 0, output_field=decimal_zero),
        )

        return Response([
            {
                'arrivage_id': arrivage.id,
                'numero_bon': arrivage.numero_bon,
                'date_arrivage': arrivage.date_arrivage.isoformat(),
                'agence': arrivage.agence.nom,
                'fournisseur': arrivage.fournisseur.nom,
                'nb_motos': arrivage.nb_motos,
                'total_revient': str(arrivage.total_revient),
                'total_vente': str(arrivage.total_vente),
                'total_marge': str(arrivage.total_vente - arrivage.total_revient),
            }
            for arrivage in arrivages
        ])
