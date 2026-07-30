from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ArrivageViewSet, MotoViewSet, StockAlertesView, StockVueEnsembleView

router = DefaultRouter()
router.register('arrivages', ArrivageViewSet, basename='arrivage')
router.register('motos', MotoViewSet, basename='moto')

urlpatterns = [
    path('stock/vue-ensemble/', StockVueEnsembleView.as_view(), name='stock-vue-ensemble'),
    path('stock/alertes/', StockAlertesView.as_view(), name='stock-alertes'),
    path('', include(router.urls)),
]
