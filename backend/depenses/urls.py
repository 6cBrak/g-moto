from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategorieDepenseViewSet, DepenseViewSet

router = DefaultRouter()
router.register('depenses', DepenseViewSet, basename='depense')
router.register('categories-depense', CategorieDepenseViewSet, basename='categoriedepense')

urlpatterns = [
    path('', include(router.urls)),
]
