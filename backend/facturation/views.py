from datetime import date, timedelta
from io import BytesIO

from django.db.models import Q
from django.http import FileResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from caisse.models import Versement
from core.models import Utilisateur
from core.pdf_utils import dessiner_entete
from core.permissions import IsAdminOrGerant
from core.utils import appliquer_periode, resolve_agence_filter
from core.viewsets import AgenceScopedViewSet
from stock.models import HistoriqueMoto, Moto

from .models import CarteGrise, Client, Declaration, DepotVente, EnvoiDepot, Facture, Quittance
from .serializers import (
    CarteGriseSerializer,
    ClientSerializer,
    DeclarationSerializer,
    DepotVenteSerializer,
    EnvoiDepotSerializer,
    FactureSerializer,
    QuittanceSerializer,
)

SEUIL_RELANCE_JOURS = 15


class ClientViewSet(AgenceScopedViewSet):
    queryset = Client.objects.select_related('agence').all()
    serializer_class = ClientSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        segment = self.request.query_params.get('segment')
        if segment:
            qs = qs.filter(segment=segment)
        return qs

    @action(detail=True, methods=['get'])
    def historique(self, request, pk=None):
        client = self.get_object()
        factures = client.factures.select_related('agence').prefetch_related(
            'lignes', 'lignes__carte_grise', 'versements',
        )
        data = []
        for facture in factures:
            total_verse = sum(
                (v.montant for v in facture.versements.all() if v.statut == Versement.Statut.VALIDE),
                start=0,
            )
            cartes_grises = [
                ligne.carte_grise for ligne in facture.lignes.all() if getattr(ligne, 'carte_grise', None)
            ]
            data.append({
                'facture_id': facture.id,
                'numero_facture': facture.numero_facture,
                'date_facture': facture.date_facture.isoformat(),
                'statut': facture.statut,
                'total': str(facture.total),
                'total_verse': str(total_verse),
                'solde': str(facture.total - total_verse),
                'nb_cartes_grises': len(cartes_grises),
                'cartes_grises_en_attente': sum(1 for c in cartes_grises if not c.retiree),
            })
        return Response({'client': ClientSerializer(client).data, 'factures': data})

    @action(detail=False, methods=['get'])
    def relances(self, request):
        agence_id = resolve_agence_filter(request)
        seuil_date = date.today() - timedelta(days=SEUIL_RELANCE_JOURS)

        cartes = CarteGrise.objects.filter(
            date_retrait__isnull=True, date_soumission__lte=seuil_date,
        ).select_related('ligne_facture__facture', 'ligne_facture__facture__client', 'ligne_facture__facture__agence')
        quittances = Quittance.objects.filter(
            date_retrait__isnull=True, date_soumission__lte=seuil_date,
        ).select_related('facture', 'facture__client', 'facture__agence')
        if agence_id:
            cartes = cartes.filter(ligne_facture__facture__agence_id=agence_id)
            quittances = quittances.filter(facture__agence_id=agence_id)

        relances = [
            {
                'type': 'carte_grise',
                'client': carte.ligne_facture.facture.client.nom,
                'facture': carte.ligne_facture.facture.numero_facture,
                'agence': carte.ligne_facture.facture.agence.nom,
                'jours_en_attente': (date.today() - carte.date_soumission).days,
            }
            for carte in cartes
        ] + [
            {
                'type': quittance.type_document,
                'client': quittance.facture.client.nom,
                'facture': quittance.facture.numero_facture,
                'agence': quittance.facture.agence.nom,
                'jours_en_attente': (date.today() - quittance.date_soumission).days,
            }
            for quittance in quittances
        ]
        relances.sort(key=lambda r: -r['jours_en_attente'])
        return Response(relances)

    @action(detail=True, methods=['get'])
    def depots_en_cours(self, request, pk=None):
        client = self.get_object()
        lignes = DepotVente.objects.filter(
            envoi__client=client, statut=DepotVente.Statut.EN_COURS,
        ).select_related('moto', 'moto__type_moto', 'moto__couleur', 'envoi')
        return Response(DepotVenteSerializer(lignes, many=True).data)


class EnvoiDepotViewSet(viewsets.ModelViewSet):
    queryset = EnvoiDepot.objects.select_related('client', 'agence', 'envoye_par').prefetch_related(
        'lignes__moto', 'lignes__moto__type_moto', 'lignes__moto__couleur',
    )
    serializer_class = EnvoiDepotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset
        if user.role != Utilisateur.Role.ADMIN:
            qs = qs.filter(agence=user.agence)
        else:
            agence_id = self.request.query_params.get('agence')
            if agence_id:
                qs = qs.filter(agence_id=agence_id)
        client_id = self.request.query_params.get('client')
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        agence = serializer.validated_data.get('agence') if user.role == Utilisateur.Role.ADMIN else user.agence
        serializer.save(agence=agence, envoye_par=user)

    @action(detail=True, methods=['get'], url_path='pdf')
    def pdf(self, request, pk=None):
        envoi = self.get_object()
        buffer = BytesIO()
        doc = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        y = dessiner_entete(doc, envoi.agence, height - 25 * mm, width)
        doc.setFont('Helvetica-Bold', 16)
        doc.drawString(20 * mm, y, "Bon de depot")
        y -= 10 * mm

        doc.setFont('Helvetica', 11)
        doc.drawString(20 * mm, y, f"Client (revendeur) : {envoi.client.nom}")
        y -= 6 * mm
        doc.drawString(20 * mm, y, f"Date : {envoi.date_envoi.strftime('%d/%m/%Y %H:%M')}")
        y -= 12 * mm

        doc.setFont('Helvetica-Bold', 10)
        doc.drawString(20 * mm, y, 'N. serie')
        doc.drawString(90 * mm, y, 'Type')
        doc.drawString(150 * mm, y, 'Couleur')
        y -= 6 * mm
        doc.setFont('Helvetica', 10)

        for ligne in envoi.lignes.all():
            doc.drawString(20 * mm, y, ligne.moto.numero_serie)
            doc.drawString(90 * mm, y, str(ligne.moto.type_moto)[:35])
            doc.drawString(150 * mm, y, ligne.moto.couleur.nom)
            y -= 6 * mm

        y -= 12 * mm
        doc.setFont('Helvetica', 10)
        doc.drawString(20 * mm, y, 'Signature revendeur : ______________________')
        doc.drawString(120 * mm, y, 'Signature agence : ______________________')

        doc.showPage()
        doc.save()
        buffer.seek(0)
        return FileResponse(
            buffer, as_attachment=False, filename=f"bon-depot-{envoi.id}.pdf",
        )


class DepotVenteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DepotVente.objects.select_related(
        'moto', 'moto__type_moto', 'moto__couleur', 'envoi', 'envoi__client', 'envoi__agence',
    )
    serializer_class = DepotVenteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset
        if user.role != Utilisateur.Role.ADMIN:
            qs = qs.filter(envoi__agence=user.agence)
        else:
            agence_id = self.request.query_params.get('agence')
            if agence_id:
                qs = qs.filter(envoi__agence_id=agence_id)
        statut = self.request.query_params.get('statut')
        if statut:
            qs = qs.filter(statut=statut)
        client_id = self.request.query_params.get('client')
        if client_id:
            qs = qs.filter(envoi__client_id=client_id)
        return qs

    @action(detail=True, methods=['post'])
    def retourner(self, request, pk=None):
        ligne = self.get_object()
        if ligne.statut != DepotVente.Statut.EN_COURS:
            return Response({'detail': 'Ce depot est deja resolu.'}, status=400)
        ligne.statut = DepotVente.Statut.RETOURNEE
        ligne.date_resolution = timezone.now()
        ligne.resolu_par = request.user
        ligne.save(update_fields=['statut', 'date_resolution', 'resolu_par'])

        moto = ligne.moto
        moto.statut = Moto.Statut.EN_STOCK
        moto.save(update_fields=['statut'])
        HistoriqueMoto.objects.create(
            moto=moto,
            type_evenement=HistoriqueMoto.TypeEvenement.RETOUR_DEPOT,
            agence_destination=moto.agence,
            utilisateur=request.user,
            commentaire=f"Retour de depot ({ligne.envoi.client.nom})",
        )
        return Response(DepotVenteSerializer(ligne).data)


def generer_numero_facture(agence):
    annee = date.today().year
    prefixe = f"F{agence.id:02d}-{annee}-"
    dernier = (
        Facture.objects.filter(numero_facture__startswith=prefixe)
        .order_by('-numero_facture')
        .first()
    )
    sequence = int(dernier.numero_facture.rsplit('-', 1)[-1]) + 1 if dernier else 1
    return f"{prefixe}{sequence:05d}"


class FactureViewSet(AgenceScopedViewSet):
    queryset = Facture.objects.select_related('agence', 'client', 'cree_par').prefetch_related(
        'lignes', 'lignes__carte_grise', 'versements',
    )
    serializer_class = FactureSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        statut = self.request.query_params.get('statut')
        if statut:
            qs = qs.filter(statut=statut)
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(Q(numero_facture__icontains=q) | Q(client__nom__icontains=q))
        return appliquer_periode(qs, 'date_facture__date', self.request)

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == Utilisateur.Role.ADMIN:
            agence = serializer.validated_data.get('agence') or user.agence
        else:
            agence = user.agence
        serializer.save(agence=agence, cree_par=user, numero_facture=generer_numero_facture(agence))

    def get_permissions(self):
        if self.action == 'annuler':
            return [IsAuthenticated(), IsAdminOrGerant()]
        return super().get_permissions()

    def update(self, request, *args, **kwargs):
        return Response(
            {'detail': "Modification non autorisee. Utilisez l'action 'annuler'."}, status=405,
        )

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return Response(
            {'detail': "Suppression non autorisee. Utilisez l'action 'annuler'."}, status=405,
        )

    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        facture = self.get_object()
        if facture.statut == Facture.Statut.ANNULEE:
            return Response({'detail': "Cette facture est deja annulee."}, status=400)

        for ligne in facture.lignes.select_related('moto').all():
            moto = ligne.moto
            if not moto:
                continue
            depot_vente = getattr(ligne, 'depot_origine', None)
            if depot_vente:
                depot_vente.statut = DepotVente.Statut.EN_COURS
                depot_vente.ligne_facture = None
                depot_vente.date_resolution = None
                depot_vente.resolu_par = None
                depot_vente.save(update_fields=['statut', 'ligne_facture', 'date_resolution', 'resolu_par'])
                moto.statut = Moto.Statut.EN_DEPOT
            else:
                moto.statut = Moto.Statut.EN_STOCK
            moto.save(update_fields=['statut'])

        facture.statut = Facture.Statut.ANNULEE
        facture.annule_par = request.user
        facture.date_annulation = timezone.now()
        facture.save(update_fields=['statut', 'annule_par', 'date_annulation'])
        return Response(FactureSerializer(facture, context={'request': request}).data)

    @action(detail=True, methods=['get'], url_path='pdf')
    def pdf(self, request, pk=None):
        facture = self.get_object()
        buffer = BytesIO()
        doc = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        y = dessiner_entete(doc, facture.agence, height - 25 * mm, width)
        doc.setFont('Helvetica-Bold', 16)
        doc.drawString(20 * mm, y, f"Facture {facture.numero_facture}")
        y -= 10 * mm

        doc.setFont('Helvetica', 11)
        doc.drawString(20 * mm, y, f"Client : {facture.client.nom}")
        y -= 6 * mm
        doc.drawString(20 * mm, y, f"Date : {facture.date_facture.strftime('%d/%m/%Y')}")
        y -= 12 * mm

        doc.setFont('Helvetica-Bold', 10)
        doc.drawString(20 * mm, y, 'Designation')
        doc.drawString(120 * mm, y, 'Qte')
        doc.drawString(140 * mm, y, 'PU')
        doc.drawString(165 * mm, y, 'Montant')
        y -= 6 * mm
        doc.setFont('Helvetica', 10)

        for ligne in facture.lignes.all():
            designation = ligne.designation
            if ligne.moto:
                designation = f"Moto {ligne.moto.numero_serie}"
            elif ligne.modele_casque:
                designation = f"Casque {ligne.modele_casque.nom}"
            doc.drawString(20 * mm, y, designation[:60])
            doc.drawString(120 * mm, y, str(ligne.quantite))
            doc.drawString(140 * mm, y, f"{ligne.prix_unitaire:,.0f}")
            doc.drawString(165 * mm, y, f"{ligne.montant:,.0f}")
            y -= 6 * mm

        y -= 6 * mm
        doc.setFont('Helvetica-Bold', 12)
        doc.drawString(120 * mm, y, f"Total : {facture.total:,.0f}")

        doc.showPage()
        doc.save()
        buffer.seek(0)
        return FileResponse(
            buffer, as_attachment=False, filename=f"{facture.numero_facture}.pdf",
        )

    @action(detail=True, methods=['get'], url_path='bordereau')
    def bordereau(self, request, pk=None):
        facture = self.get_object()
        buffer = BytesIO()
        doc = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        y = dessiner_entete(doc, facture.agence, height - 25 * mm, width)
        doc.setFont('Helvetica-Bold', 16)
        doc.drawString(20 * mm, y, f"Bordereau de livraison - {facture.numero_facture}")
        y -= 10 * mm

        doc.setFont('Helvetica', 11)
        doc.drawString(20 * mm, y, f"Client : {facture.client.nom}")
        y -= 6 * mm
        doc.drawString(20 * mm, y, f"Adresse : {facture.client.adresse}")
        y -= 12 * mm

        doc.setFont('Helvetica-Bold', 10)
        doc.drawString(20 * mm, y, 'Article a livrer')
        doc.drawString(150 * mm, y, 'Qte')
        y -= 6 * mm
        doc.setFont('Helvetica', 10)

        for ligne in facture.lignes.all():
            if ligne.moto:
                designation = f"Moto {ligne.moto.numero_serie} - {ligne.moto.type_moto}"
            elif ligne.modele_casque:
                designation = f"Casque {ligne.modele_casque.nom}"
            else:
                designation = ligne.designation
            doc.drawString(20 * mm, y, designation[:80])
            doc.drawString(150 * mm, y, str(ligne.quantite))
            y -= 6 * mm

        y -= 12 * mm
        doc.setFont('Helvetica', 10)
        doc.drawString(20 * mm, y, 'Signature client : ______________________')
        doc.drawString(120 * mm, y, 'Signature agence : ______________________')

        doc.showPage()
        doc.save()
        buffer.seek(0)
        return FileResponse(
            buffer, as_attachment=False, filename=f"bordereau-{facture.numero_facture}.pdf",
        )


class DeclarationViewSet(viewsets.ModelViewSet):
    serializer_class = DeclarationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Declaration.objects.select_related('facture', 'facture__agence')
        if user.role != Utilisateur.Role.ADMIN:
            qs = qs.filter(facture__agence=user.agence)
        facture_id = self.request.query_params.get('facture')
        if facture_id:
            qs = qs.filter(facture_id=facture_id)
        return qs


class CarteGriseViewSet(viewsets.ModelViewSet):
    serializer_class = CarteGriseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = CarteGrise.objects.select_related(
            'ligne_facture__facture', 'ligne_facture__facture__agence', 'ligne_facture__moto',
        )
        if user.role != Utilisateur.Role.ADMIN:
            qs = qs.filter(ligne_facture__facture__agence=user.agence)
        facture_id = self.request.query_params.get('facture')
        if facture_id:
            qs = qs.filter(ligne_facture__facture_id=facture_id)
        return qs

    @action(detail=True, methods=['post'])
    def recevoir(self, request, pk=None):
        carte_grise = self.get_object()
        carte_grise.date_reception = date.today()
        carte_grise.save(update_fields=['date_reception'])
        return Response(CarteGriseSerializer(carte_grise).data)

    @action(detail=True, methods=['post'])
    def retirer(self, request, pk=None):
        carte_grise = self.get_object()
        carte_grise.date_retrait = timezone.now()
        carte_grise.retirer_nom = request.data.get('retirer_nom', '')
        carte_grise.retirer_telephone = request.data.get('retirer_telephone', '')
        carte_grise.save(update_fields=['date_retrait', 'retirer_nom', 'retirer_telephone'])
        return Response(CarteGriseSerializer(carte_grise).data)


class QuittanceViewSet(viewsets.ModelViewSet):
    serializer_class = QuittanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Quittance.objects.select_related('facture', 'facture__agence')
        if user.role != Utilisateur.Role.ADMIN:
            qs = qs.filter(facture__agence=user.agence)
        facture_id = self.request.query_params.get('facture')
        if facture_id:
            qs = qs.filter(facture_id=facture_id)
        return qs

    @action(detail=True, methods=['post'])
    def retirer(self, request, pk=None):
        quittance = self.get_object()
        quittance.date_retrait = timezone.now()
        quittance.retirer_nom = request.data.get('retirer_nom', '')
        quittance.retirer_telephone = request.data.get('retirer_telephone', '')
        quittance.save(update_fields=['date_retrait', 'retirer_nom', 'retirer_telephone'])
        return Response(QuittanceSerializer(quittance).data)
