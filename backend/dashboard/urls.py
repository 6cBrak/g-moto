from django.urls import path

from .views import (
    DashboardKPIsView,
    RapportComparatifAgencesView,
    RapportComparatifPeriodeView,
    RapportMargeArrivagesView,
)

urlpatterns = [
    path('dashboard/kpis/', DashboardKPIsView.as_view(), name='dashboard-kpis'),
    path(
        'dashboard/comparatif-periode/',
        RapportComparatifPeriodeView.as_view(),
        name='dashboard-comparatif-periode',
    ),
    path(
        'dashboard/comparatif-agences/',
        RapportComparatifAgencesView.as_view(),
        name='dashboard-comparatif-agences',
    ),
    path(
        'dashboard/marge-arrivages/',
        RapportMargeArrivagesView.as_view(),
        name='dashboard-marge-arrivages',
    ),
]
