from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EntretienViewSet, EntretiensAVenirView, GarantieViewSet

router = DefaultRouter()
router.register('garanties', GarantieViewSet, basename='garantie')
router.register('entretiens', EntretienViewSet, basename='entretien')

urlpatterns = [
    path('apresvente/entretiens-a-venir/', EntretiensAVenirView.as_view(), name='entretiens-a-venir'),
    path('', include(router.urls)),
]
