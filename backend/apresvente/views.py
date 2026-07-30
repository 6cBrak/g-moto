from datetime import date, timedelta

from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Utilisateur
from core.utils import appliquer_periode, resolve_agence_filter

from .models import Entretien, Garantie
from .serializers import EntretienSerializer, GarantieSerializer


class MotoScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == Utilisateur.Role.ADMIN:
            qs = self.queryset
            agence_id = self.request.query_params.get('agence')
            if agence_id:
                qs = qs.filter(moto__agence_id=agence_id)
            return qs
        return self.queryset.filter(moto__agence=user.agence)

    def perform_create(self, serializer):
        serializer.save(cree_par=self.request.user)


class GarantieViewSet(MotoScopedViewSet):
    queryset = Garantie.objects.select_related('moto', 'moto__agence', 'cree_par')
    serializer_class = GarantieSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(moto__numero_serie__icontains=q)
        return appliquer_periode(qs, 'date_debut', self.request)


class EntretienViewSet(MotoScopedViewSet):
    queryset = Entretien.objects.select_related('moto', 'moto__agence', 'cree_par')
    serializer_class = EntretienSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(moto__numero_serie__icontains=q)
        statut = self.request.query_params.get('statut')
        if statut == 'realise':
            qs = qs.filter(date_realisee__isnull=False)
        elif statut == 'a_faire':
            qs = qs.filter(date_realisee__isnull=True)
        return appliquer_periode(qs, 'date_prevue', self.request)

    @action(detail=True, methods=['post'])
    def realiser(self, request, pk=None):
        entretien = self.get_object()
        entretien.date_realisee = date.today()
        entretien.save(update_fields=['date_realisee'])
        return Response(EntretienSerializer(entretien).data)


class EntretiensAVenirView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agence_id = resolve_agence_filter(request)
        jours = int(request.query_params.get('jours', 30))
        date_limite = date.today() + timedelta(days=jours)

        entretiens = Entretien.objects.select_related('moto', 'moto__agence').filter(
            date_realisee__isnull=True, date_prevue__lte=date_limite,
        )
        if agence_id:
            entretiens = entretiens.filter(moto__agence_id=agence_id)

        return Response(EntretienSerializer(entretiens, many=True).data)
