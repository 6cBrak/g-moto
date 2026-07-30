from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.permissions import IsAdminOrGerant

from .models import Couleur, Fournisseur, Marque, ModeleCasque, TypeMoto
from .serializers import (
    CouleurSerializer,
    FournisseurSerializer,
    MarqueSerializer,
    ModeleCasqueSerializer,
    TypeMotoSerializer,
)


class CatalogueViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsAdminOrGerant()]
        return [IsAuthenticated()]


class MarqueViewSet(CatalogueViewSet):
    queryset = Marque.objects.all()
    serializer_class = MarqueSerializer


class CouleurViewSet(CatalogueViewSet):
    queryset = Couleur.objects.all()
    serializer_class = CouleurSerializer


class TypeMotoViewSet(CatalogueViewSet):
    queryset = TypeMoto.objects.select_related('marque').all()
    serializer_class = TypeMotoSerializer


class ModeleCasqueViewSet(CatalogueViewSet):
    queryset = ModeleCasque.objects.all()
    serializer_class = ModeleCasqueSerializer


class FournisseurViewSet(CatalogueViewSet):
    queryset = Fournisseur.objects.all()
    serializer_class = FournisseurSerializer
