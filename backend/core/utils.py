from decimal import Decimal

from django.db.models import Sum

from .models import Utilisateur


def resolve_agence_filter(request):
    user = request.user
    if user.role == Utilisateur.Role.ADMIN:
        agence_id = request.query_params.get('agence')
        return int(agence_id) if agence_id else None
    return user.agence_id


def appliquer_periode(queryset, champ_date, request):
    date_debut = request.query_params.get('date_debut')
    date_fin = request.query_params.get('date_fin')
    if date_debut:
        queryset = queryset.filter(**{f'{champ_date}__gte': date_debut})
    if date_fin:
        queryset = queryset.filter(**{f'{champ_date}__lte': date_fin})
    return queryset


def compter_donnees_commerciales():
    from caisse.models import SessionCaisse, SortieCaisse, Versement
    from facturation.models import (
        CarteGrise, Client, Declaration, DepotVente, EnvoiDepot, Facture,
        LigneFacture, Quittance,
    )
    from stock.models import Moto

    return {
        'versements': Versement.objects.count(),
        'sorties_caisse': SortieCaisse.objects.count(),
        'sessions_caisse': SessionCaisse.objects.count(),
        'quittances': Quittance.objects.count(),
        'cartes_grises': CarteGrise.objects.count(),
        'declarations': Declaration.objects.count(),
        'depots_vente': DepotVente.objects.count(),
        'envois_depot': EnvoiDepot.objects.count(),
        'lignes_facture': LigneFacture.objects.count(),
        'factures': Facture.objects.count(),
        'clients': Client.objects.count(),
        'motos_a_remettre_en_stock': Moto.objects.filter(
            statut__in=[Moto.Statut.VENDUE, Moto.Statut.EN_DEPOT],
        ).count(),
    }


def purger_donnees_commerciales():
    """Supprime les donnees commerciales de test avant le lancement en production.

    Vide factures (et documents lies), caisse, clients et depots-vente. Le
    module stock n'est pas touche, hormis la remise en stock des motos
    vendues/en depot (leur facture ou depot disparaissant, elles doivent
    redevenir disponibles).
    """
    from django.db import transaction

    from caisse.models import SessionCaisse, SortieCaisse, Versement
    from facturation.models import Client, DepotVente, EnvoiDepot, Facture
    from stock.models import Moto

    counts = compter_donnees_commerciales()
    with transaction.atomic():
        Versement.objects.all().delete()
        SortieCaisse.objects.all().delete()
        SessionCaisse.objects.all().delete()
        DepotVente.objects.all().delete()
        EnvoiDepot.objects.all().delete()
        Facture.objects.all().delete()
        Client.objects.all().delete()
        Moto.objects.filter(
            statut__in=[Moto.Statut.VENDUE, Moto.Statut.EN_DEPOT],
        ).update(statut=Moto.Statut.EN_STOCK)
    return counts


def calculer_fournisseurs_dus(agence_id=None):
    """Etat des motos recues en depot (arrivages marques en_depot=True) par fournisseur.

    Une moto en depot ne represente une dette envers le fournisseur qu'une
    fois vendue (avant, elle n'est pas encore due). Le "reste a payer" tient
    compte des reglements deja enregistres via SortieCaisse.
    """
    from caisse.models import SortieCaisse
    from catalogue.models import Fournisseur
    from stock.models import Moto

    fournisseurs = Fournisseur.objects.filter(arrivages__en_depot=True).distinct()

    dus = []
    for fournisseur in fournisseurs:
        motos = Moto.objects.filter(arrivage__fournisseur=fournisseur, arrivage__en_depot=True)
        if agence_id:
            motos = motos.filter(agence_id=agence_id)

        en_stock = motos.filter(statut=Moto.Statut.EN_STOCK)
        vendues = motos.filter(statut=Moto.Statut.VENDUE)
        valeur_en_stock = en_stock.aggregate(total=Sum('prix_achat'))['total'] or Decimal('0')
        valeur_due = vendues.aggregate(total=Sum('prix_achat'))['total'] or Decimal('0')

        reglements = SortieCaisse.objects.filter(
            fournisseur=fournisseur, motif=SortieCaisse.Motif.REGLEMENT_FOURNISSEUR,
        )
        if agence_id:
            reglements = reglements.filter(agence_id=agence_id)
        deja_regle = reglements.aggregate(total=Sum('montant'))['total'] or Decimal('0')

        nb_en_stock = en_stock.count()
        nb_vendues = vendues.count()
        if nb_en_stock or nb_vendues or deja_regle:
            dus.append({
                'fournisseur_id': fournisseur.id,
                'fournisseur_nom': fournisseur.nom,
                'nb_motos_en_stock': nb_en_stock,
                'valeur_en_stock': valeur_en_stock,
                'nb_motos_vendues': nb_vendues,
                'valeur_due': valeur_due,
                'deja_regle': deja_regle,
                'reste_a_payer': valeur_due - deja_regle,
            })
    return dus


def calculer_clients_debiteurs(agence_id=None, nom=None):
    """Liste des clients dont le solde (facture - verse) est positif.

    Boucle par client plutot qu'un unique queryset annote : sommer
    factures__lignes__montant et factures__versements__montant dans le
    meme annotate() provoquerait un fan-out de jointure qui fausserait
    les deux totaux.
    """
    from caisse.models import Versement
    from facturation.models import Client, Facture, LigneFacture

    clients = Client.objects.select_related('agence')
    if agence_id:
        clients = clients.filter(agence_id=agence_id)
    if nom:
        clients = clients.filter(nom__icontains=nom)

    debiteurs = []
    for client in clients:
        total_facture = LigneFacture.objects.filter(
            facture__client=client, facture__statut=Facture.Statut.VALIDEE,
        ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
        total_verse = Versement.objects.filter(
            facture__client=client,
        ).exclude(statut=Versement.Statut.ANNULE).aggregate(total=Sum('montant'))['total'] or Decimal('0')
        solde = total_facture - total_verse
        if solde > 0:
            debiteurs.append({
                'client_id': client.id,
                'client_nom': client.nom,
                'agence': client.agence.nom,
                'total_facture': total_facture,
                'total_verse': total_verse,
                'solde': solde,
            })
    return debiteurs
