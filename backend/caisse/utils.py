from datetime import date
from decimal import Decimal

from django.db.models import Sum
from rest_framework.exceptions import ValidationError


def verifier_caisse_ouverte(agence):
    from .models import SessionCaisse

    ouverte = SessionCaisse.objects.filter(
        agence=agence, date_session=date.today(), date_fermeture__isnull=True,
    ).exists()
    if not ouverte:
        raise ValidationError({'detail': "La caisse du jour n'est pas ouverte pour cette agence."})


def verifier_solde_suffisant(agence, montant):
    """Refuse une depense/sortie qui ferait passer le solde theorique du jour sous 0."""
    from .models import SessionCaisse

    session = SessionCaisse.objects.filter(
        agence=agence, date_session=date.today(), date_fermeture__isnull=True,
    ).first()
    if not session:
        return
    theorique = calculer_montant_theorique(session)
    if montant > theorique:
        raise ValidationError({
            'montant': f"Solde de caisse insuffisant (theorique actuel : {theorique} F).",
        })


def calculer_montant_theorique(session):
    from depenses.models import Depense

    from .models import SortieCaisse, Versement

    encaissements = Versement.objects.filter(
        agence=session.agence, date_versement__date=session.date_session,
    ).exclude(statut=Versement.Statut.ANNULE).aggregate(total=Sum('montant'))['total'] or Decimal('0')
    depenses = Depense.objects.filter(
        agence=session.agence, date_depense=session.date_session,
    ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
    sorties = SortieCaisse.objects.filter(
        agence=session.agence, date_sortie__date=session.date_session,
    ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
    return session.montant_ouverture + encaissements - depenses - sorties
