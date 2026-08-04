from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ClientsDebiteursView,
    FournisseursDusView,
    HistoriqueSerieView,
    JournalCaisseView,
    RapportDepensesView,
    RapportVentesParClientView,
    RapportVentesView,
    SessionCaisseViewSet,
    SortieCaisseViewSet,
    VersementViewSet,
)

router = DefaultRouter()
router.register('versements', VersementViewSet, basename='versement')
router.register('sorties-caisse', SortieCaisseViewSet, basename='sortie-caisse')
router.register('sessions-caisse', SessionCaisseViewSet, basename='session-caisse')

urlpatterns = [
    path('caisse/journal/', JournalCaisseView.as_view(), name='caisse-journal'),
    path('caisse/rapport-ventes/', RapportVentesView.as_view(), name='caisse-rapport-ventes'),
    path('caisse/rapport-depenses/', RapportDepensesView.as_view(), name='caisse-rapport-depenses'),
    path('caisse/clients-debiteurs/', ClientsDebiteursView.as_view(), name='caisse-clients-debiteurs'),
    path('caisse/fournisseurs-dus/', FournisseursDusView.as_view(), name='caisse-fournisseurs-dus'),
    path(
        'caisse/rapport-ventes-clients/',
        RapportVentesParClientView.as_view(),
        name='caisse-rapport-ventes-clients',
    ),
    path('caisse/historique-serie/', HistoriqueSerieView.as_view(), name='caisse-historique-serie'),
    path('', include(router.urls)),
]
