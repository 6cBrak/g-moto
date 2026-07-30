from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CouleurViewSet,
    FournisseurViewSet,
    MarqueViewSet,
    ModeleCasqueViewSet,
    TypeMotoViewSet,
)

router = DefaultRouter()
router.register('marques', MarqueViewSet, basename='marque')
router.register('couleurs', CouleurViewSet, basename='couleur')
router.register('types-moto', TypeMotoViewSet, basename='typemoto')
router.register('modeles-casque', ModeleCasqueViewSet, basename='modelecasque')
router.register('fournisseurs', FournisseurViewSet, basename='fournisseur')

urlpatterns = [
    path('', include(router.urls)),
]
