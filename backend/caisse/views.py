from datetime import date
from decimal import Decimal, InvalidOperation
from io import BytesIO

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from core.models import Agence, Utilisateur
from core.pdf_utils import dessiner_entete
from core.utils import appliquer_periode, calculer_clients_debiteurs, resolve_agence_filter
from core.viewsets import AgenceScopedViewSet
from depenses.models import Depense
from facturation.models import Facture, LigneFacture
from stock.models import Moto
from stock.serializers import HistoriqueMotoSerializer, MotoSerializer

from .models import SessionCaisse, SortieCaisse, Versement
from .serializers import SessionCaisseSerializer, SortieCaisseSerializer, VersementSerializer
from .utils import verifier_caisse_ouverte


class VersementViewSet(AgenceScopedViewSet):
    queryset = Versement.objects.select_related('facture', 'facture__client', 'agence', 'cree_par')
    serializer_class = VersementSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        facture_id = self.request.query_params.get('facture')
        if facture_id:
            qs = qs.filter(facture_id=facture_id)
        return qs

    def perform_create(self, serializer):
        facture = serializer.validated_data['facture']
        verifier_caisse_ouverte(facture.agence)
        serializer.save(agence=facture.agence, cree_par=self.request.user)

    @action(detail=True, methods=['get'], url_path='recu')
    def recu(self, request, pk=None):
        versement = self.get_object()
        buffer = BytesIO()
        doc = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        y = dessiner_entete(doc, versement.agence, height - 25 * mm, width)
        doc.setFont('Helvetica-Bold', 16)
        doc.drawString(20 * mm, y, "Recu de versement")
        y -= 12 * mm

        doc.setFont('Helvetica', 11)
        for ligne in [
            f"Facture : {versement.facture.numero_facture}",
            f"Client : {versement.facture.client.nom}",
            f"Date : {versement.date_versement.strftime('%d/%m/%Y %H:%M')}",
            f"Mode de paiement : {versement.get_mode_paiement_display()}",
            f"Reference : {versement.reference_transaction or '-'}",
            f"Recu par : {versement.cree_par.username}",
        ]:
            doc.drawString(20 * mm, y, ligne)
            y -= 7 * mm

        y -= 8 * mm
        doc.setFont('Helvetica-Bold', 14)
        doc.drawString(20 * mm, y, f"Montant verse : {versement.montant:,.0f} F")

        y -= 20 * mm
        doc.setFont('Helvetica', 10)
        doc.drawString(20 * mm, y, 'Signature : ______________________')

        doc.showPage()
        doc.save()
        buffer.seek(0)
        return FileResponse(
            buffer, as_attachment=False, filename=f"recu-versement-{versement.id}.pdf",
        )


class SortieCaisseViewSet(AgenceScopedViewSet):
    queryset = SortieCaisse.objects.select_related('agence', 'cree_par')
    serializer_class = SortieCaisseSerializer

    def perform_create(self, serializer):
        user = self.request.user
        agence = serializer.validated_data.get('agence') if user.role == Utilisateur.Role.ADMIN else user.agence
        verifier_caisse_ouverte(agence)
        if user.role == Utilisateur.Role.ADMIN:
            serializer.save(agence=agence, cree_par=user)
        else:
            serializer.save(agence=user.agence, cree_par=user)


class SessionCaisseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SessionCaisseSerializer
    permission_classes = [IsAuthenticated]
    queryset = SessionCaisse.objects.select_related('agence', 'ouvert_par', 'ferme_par')

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset
        if user.role == Utilisateur.Role.ADMIN:
            agence_id = self.request.query_params.get('agence')
            if agence_id:
                qs = qs.filter(agence_id=agence_id)
            return qs
        return qs.filter(agence=user.agence)

    def _agence_pour_ecriture(self, request):
        user = request.user
        if user.role == Utilisateur.Role.ADMIN:
            agence_id = request.data.get('agence') or request.query_params.get('agence')
            if not agence_id:
                raise ValidationError({'agence': 'Ce champ est requis pour un administrateur.'})
            return get_object_or_404(Agence, pk=agence_id)
        return user.agence

    @action(detail=False, methods=['get'])
    def courante(self, request):
        user = request.user
        if user.role == Utilisateur.Role.ADMIN:
            agence_id = request.query_params.get('agence')
            if not agence_id:
                return Response({'detail': 'Le parametre agence est requis pour un administrateur.'}, status=400)
            agence = get_object_or_404(Agence, pk=agence_id)
        else:
            agence = user.agence

        aujourdhui = date.today()
        session = SessionCaisse.objects.filter(agence=agence, date_session=aujourdhui).first()
        derniere_fermeture = (
            SessionCaisse.objects.filter(agence=agence, date_fermeture__isnull=False)
            .order_by('-date_session')
            .first()
        )
        solde_precedent = derniere_fermeture.montant_fermeture if derniere_fermeture else Decimal('0')

        return Response({
            'session': SessionCaisseSerializer(session).data if session else None,
            'solde_precedent': str(solde_precedent),
        })

    @action(detail=False, methods=['post'])
    def ouvrir(self, request):
        agence = self._agence_pour_ecriture(request)
        aujourdhui = date.today()
        if SessionCaisse.objects.filter(agence=agence, date_session=aujourdhui).exists():
            return Response({'detail': 'La caisse du jour est deja ouverte pour cette agence.'}, status=400)

        montant_ouverture = request.data.get('montant_ouverture')
        if montant_ouverture in (None, ''):
            return Response({'detail': 'montant_ouverture est requis.'}, status=400)
        try:
            montant_ouverture = Decimal(str(montant_ouverture))
        except InvalidOperation:
            return Response({'detail': 'montant_ouverture doit etre un nombre.'}, status=400)

        session = SessionCaisse.objects.create(
            agence=agence,
            date_session=aujourdhui,
            montant_ouverture=montant_ouverture,
            ouvert_par=request.user,
            commentaire=request.data.get('commentaire', ''),
        )
        return Response(SessionCaisseSerializer(session).data, status=201)

    @action(detail=True, methods=['post'])
    def fermer(self, request, pk=None):
        session = self.get_object()
        if session.date_fermeture is not None:
            return Response({'detail': 'Cette session est deja fermee.'}, status=400)

        montant_fermeture = request.data.get('montant_fermeture')
        if montant_fermeture in (None, ''):
            return Response({'detail': 'montant_fermeture est requis.'}, status=400)
        try:
            montant_fermeture = Decimal(str(montant_fermeture))
        except InvalidOperation:
            return Response({'detail': 'montant_fermeture doit etre un nombre.'}, status=400)

        session.montant_fermeture = montant_fermeture
        session.ferme_par = request.user
        session.date_fermeture = timezone.now()
        if request.data.get('commentaire'):
            session.commentaire = request.data.get('commentaire')
        session.save(update_fields=['montant_fermeture', 'ferme_par', 'date_fermeture', 'commentaire'])
        return Response(SessionCaisseSerializer(session).data)

    @action(detail=True, methods=['post'])
    def reouvrir(self, request, pk=None):
        session = self.get_object()
        if session.date_fermeture is None:
            return Response({'detail': 'Cette session est deja ouverte.'}, status=400)

        session.montant_fermeture = None
        session.ferme_par = None
        session.date_fermeture = None
        session.save(update_fields=['montant_fermeture', 'ferme_par', 'date_fermeture'])
        return Response(SessionCaisseSerializer(session).data)


class JournalCaisseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agence_id = resolve_agence_filter(request)

        versements = Versement.objects.select_related('facture', 'agence')
        depenses = Depense.objects.select_related('agence')
        sorties = SortieCaisse.objects.select_related('agence')
        if agence_id:
            versements = versements.filter(agence_id=agence_id)
            depenses = depenses.filter(agence_id=agence_id)
            sorties = sorties.filter(agence_id=agence_id)
        versements = appliquer_periode(versements, 'date_versement__date', request)
        depenses = appliquer_periode(depenses, 'date_depense', request)
        sorties = appliquer_periode(sorties, 'date_sortie__date', request)

        mouvements = [
            {
                'type': 'encaissement',
                'date': v.date_versement.isoformat(),
                'montant': str(v.montant),
                'agence': v.agence.nom,
                'description': f"Versement facture {v.facture.numero_facture} ({v.get_mode_paiement_display()})",
            }
            for v in versements
        ] + [
            {
                'type': 'decaissement',
                'date': d.date_depense.isoformat(),
                'montant': str(-d.montant),
                'agence': d.agence.nom,
                'description': d.description or d.get_categorie_display(),
            }
            for d in depenses
        ] + [
            {
                'type': 'decaissement',
                'date': s.date_sortie.isoformat(),
                'montant': str(-s.montant),
                'agence': s.agence.nom,
                'description': s.description or s.get_motif_display(),
            }
            for s in sorties
        ]
        mouvements.sort(key=lambda m: m['date'], reverse=True)

        q = request.query_params.get('q')
        if q:
            mouvements = [m for m in mouvements if q.lower() in m['description'].lower()]

        return Response(mouvements)


class RapportVentesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agence_id = resolve_agence_filter(request)
        factures = Facture.objects.filter(statut=Facture.Statut.VALIDEE)
        if agence_id:
            factures = factures.filter(agence_id=agence_id)
        factures = appliquer_periode(factures, 'date_facture__date', request)

        total = LigneFacture.objects.filter(facture__in=factures).aggregate(total=Sum('montant'))['total'] or 0
        return Response({'nb_factures': factures.count(), 'total_ventes': str(total)})


class RapportDepensesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agence_id = resolve_agence_filter(request)
        depenses = Depense.objects.all()
        if agence_id:
            depenses = depenses.filter(agence_id=agence_id)
        depenses = appliquer_periode(depenses, 'date_depense', request)

        total = depenses.aggregate(total=Sum('montant'))['total'] or 0
        par_categorie = list(
            depenses.values('categorie').annotate(total=Sum('montant')).order_by('-total'),
        )
        return Response({'total_depenses': str(total), 'par_categorie': par_categorie})


class ClientsDebiteursView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agence_id = resolve_agence_filter(request)
        nom = request.query_params.get('q')
        debiteurs = calculer_clients_debiteurs(agence_id, nom=nom)
        return Response([
            {
                **d,
                'total_facture': str(d['total_facture']),
                'total_verse': str(d['total_verse']),
                'solde': str(d['solde']),
            }
            for d in debiteurs
        ])


class RapportVentesParClientView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agence_id = resolve_agence_filter(request)
        factures = Facture.objects.filter(statut=Facture.Statut.VALIDEE)
        if agence_id:
            factures = factures.filter(agence_id=agence_id)
        factures = appliquer_periode(factures, 'date_facture__date', request)

        data = (
            LigneFacture.objects.filter(facture__in=factures)
            .values('facture__client__id', 'facture__client__nom')
            .annotate(total=Sum('montant'))
            .order_by('-total')
        )
        return Response([
            {'client_id': row['facture__client__id'], 'client_nom': row['facture__client__nom'], 'total': str(row['total'])}
            for row in data
        ])


class HistoriqueSerieView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        numero_serie = request.query_params.get('numero_serie')
        if not numero_serie:
            return Response({'detail': 'Le parametre numero_serie est requis.'}, status=400)

        moto = get_object_or_404(Moto, numero_serie=numero_serie)
        user = request.user
        if user.role != Utilisateur.Role.ADMIN and moto.agence_id != user.agence_id:
            return Response({'detail': 'Not found.'}, status=404)

        return Response({
            'moto': MotoSerializer(moto).data,
            'historique': HistoriqueMotoSerializer(moto.historique.all(), many=True).data,
        })
