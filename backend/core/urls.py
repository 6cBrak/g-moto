from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AgenceViewSet, MeView, PurgeDonneesCommercialesView, UtilisateurViewSet

router = DefaultRouter()
router.register('agences', AgenceViewSet, basename='agence')
router.register('utilisateurs', UtilisateurViewSet, basename='utilisateur')

urlpatterns = [
    path('auth/me/', MeView.as_view(), name='me'),
    path(
        'admin/purge-donnees-commerciales/', PurgeDonneesCommercialesView.as_view(),
        name='purge-donnees-commerciales',
    ),
    path('', include(router.urls)),
]
