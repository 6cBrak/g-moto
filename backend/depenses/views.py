from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from caisse.utils import verifier_caisse_ouverte, verifier_solde_suffisant
from core.models import Utilisateur
from core.permissions import IsAdminOrGerant
from core.utils import appliquer_periode
from core.viewsets import AgenceScopedViewSet

from .models import CategorieDepense, Depense
from .serializers import CategorieDepenseSerializer, DepenseSerializer


class CategorieDepenseViewSet(viewsets.ModelViewSet):
    queryset = CategorieDepense.objects.all()
    serializer_class = CategorieDepenseSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsAdminOrGerant()]
        return [IsAuthenticated()]


class DepenseViewSet(AgenceScopedViewSet):
    queryset = Depense.objects.select_related('agence', 'categorie', 'cree_par').all()
    serializer_class = DepenseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        categorie = self.request.query_params.get('categorie')
        if categorie:
            qs = qs.filter(categorie=categorie)
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(description__icontains=q)
        return appliquer_periode(qs, 'date_depense', self.request)

    def perform_create(self, serializer):
        user = self.request.user
        agence = serializer.validated_data.get('agence') if user.role == Utilisateur.Role.ADMIN else user.agence
        verifier_caisse_ouverte(agence)
        verifier_solde_suffisant(agence, serializer.validated_data['montant'])
        if user.role == Utilisateur.Role.ADMIN:
            serializer.save(cree_par=user)
        else:
            serializer.save(agence=user.agence, cree_par=user)
