from django.db import transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Utilisateur
from core.permissions import IsAdminOrGerant
from core.utils import appliquer_periode, resolve_agence_filter
from core.viewsets import AgenceScopedViewSet

from .models import Arrivage, HistoriqueMoto, Moto
from .serializers import (
    ArrivageSerializer,
    HistoriqueMotoSerializer,
    MotoSerializer,
    TransfertSerializer,
)


class ArrivageViewSet(AgenceScopedViewSet):
    queryset = Arrivage.objects.select_related('agence', 'fournisseur', 'cree_par').all()
    serializer_class = ArrivageSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == Utilisateur.Role.ADMIN:
            serializer.save(cree_par=user)
        else:
            serializer.save(agence=user.agence, cree_par=user)


class MotoViewSet(AgenceScopedViewSet):
    queryset = Moto.objects.select_related('type_moto', 'type_moto__marque', 'couleur', 'agence', 'arrivage').all()
    serializer_class = MotoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        arrivage_id = self.request.query_params.get('arrivage')
        if arrivage_id:
            qs = qs.filter(arrivage_id=arrivage_id)
        statut = self.request.query_params.get('statut')
        if statut:
            qs = qs.filter(statut=statut)
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(Q(numero_serie__icontains=q) | Q(immatriculation__icontains=q))
        return appliquer_periode(qs, 'date_creation__date', self.request)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        HistoriqueMoto.objects.create(
            moto=serializer.instance,
            type_evenement=HistoriqueMoto.TypeEvenement.ARRIVAGE,
            agence_destination=serializer.instance.agence,
            utilisateur=self.request.user,
        )

    def update(self, request, *args, **kwargs):
        moto = self.get_object()
        if moto.statut == Moto.Statut.VENDUE:
            return Response({'detail': "Impossible de modifier une moto vendue."}, status=400)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        moto = self.get_object()
        if moto.statut == Moto.Statut.VENDUE:
            return Response({'detail': "Impossible de supprimer une moto vendue."}, status=400)
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {'detail': "Cette moto est liee a d'autres enregistrements (depot, historique) et ne peut pas etre supprimee."},
                status=400,
            )

    @action(detail=True, methods=['get'])
    def historique(self, request, pk=None):
        moto = self.get_object()
        events = moto.historique.all()
        return Response(HistoriqueMotoSerializer(events, many=True).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrGerant])
    def transferer(self, request, pk=None):
        moto = self.get_object()
        serializer = TransfertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        destination = serializer.validated_data['agence_destination']
        commentaire = serializer.validated_data.get('commentaire', '')

        with transaction.atomic():
            agence_source = moto.agence
            moto.agence = destination
            moto.save(update_fields=['agence'])
            HistoriqueMoto.objects.create(
                moto=moto,
                type_evenement=HistoriqueMoto.TypeEvenement.TRANSFERT,
                agence_source=agence_source,
                agence_destination=destination,
                utilisateur=request.user,
                commentaire=commentaire,
            )
        return Response(MotoSerializer(moto).data)


class StockVueEnsembleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agence_id = resolve_agence_filter(request)
        qs = Moto.objects.filter(statut=Moto.Statut.EN_STOCK)
        if agence_id:
            qs = qs.filter(agence_id=agence_id)

        par_agence = list(
            qs.values('agence_id', 'agence__nom')
            .annotate(quantite=Count('id'))
            .order_by('agence__nom'),
        )
        par_type = list(
            qs.values('type_moto_id', 'type_moto__nom', 'type_moto__marque__nom')
            .annotate(quantite=Count('id'))
            .order_by('-quantite'),
        )
        return Response({
            'total_en_stock': qs.count(),
            'par_agence': par_agence,
            'par_type': par_type,
        })


class StockAlertesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agence_id = resolve_agence_filter(request)

        en_stock = Moto.objects.filter(statut=Moto.Statut.EN_STOCK)
        if agence_id:
            en_stock = en_stock.filter(agence_id=agence_id)
        en_stock_counts = {
            (row['agence_id'], row['type_moto_id']): row['quantite']
            for row in en_stock.values('agence_id', 'type_moto_id').annotate(quantite=Count('id'))
        }

        combos = Moto.objects.values(
            'agence_id', 'agence__nom', 'type_moto_id', 'type_moto__nom', 'type_moto__seuil_alerte',
        ).distinct()
        if agence_id:
            combos = combos.filter(agence_id=agence_id)

        alertes = []
        for combo in combos:
            quantite = en_stock_counts.get((combo['agence_id'], combo['type_moto_id']), 0)
            seuil = combo['type_moto__seuil_alerte'] or 0
            if quantite < seuil:
                alertes.append({
                    'agence': combo['agence__nom'],
                    'type_moto': combo['type_moto__nom'],
                    'quantite_stock': quantite,
                    'seuil_alerte': seuil,
                })
        return Response(alertes)
