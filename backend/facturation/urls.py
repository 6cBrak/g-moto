from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CarteGriseViewSet,
    ClientViewSet,
    DeclarationViewSet,
    DepotVenteViewSet,
    EnvoiDepotViewSet,
    FactureViewSet,
    QuittanceViewSet,
)

router = DefaultRouter()
router.register('clients', ClientViewSet, basename='client')
router.register('factures', FactureViewSet, basename='facture')
router.register('declarations', DeclarationViewSet, basename='declaration')
router.register('cartes-grises', CarteGriseViewSet, basename='cartegrise')
router.register('quittances', QuittanceViewSet, basename='quittance')
router.register('envois-depot', EnvoiDepotViewSet, basename='envoidepot')
router.register('depots', DepotVenteViewSet, basename='depotvente')

urlpatterns = [
    path('', include(router.urls)),
]
