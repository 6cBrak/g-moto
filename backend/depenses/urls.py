from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DepenseViewSet

router = DefaultRouter()
router.register('depenses', DepenseViewSet, basename='depense')

urlpatterns = [
    path('', include(router.urls)),
]
