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
        ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
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
