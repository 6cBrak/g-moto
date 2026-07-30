from django.contrib import admin

from .models import Entretien, Garantie


@admin.register(Garantie)
class GarantieAdmin(admin.ModelAdmin):
    list_display = ('moto', 'date_debut', 'duree_mois', 'date_fin', 'active')
    search_fields = ('moto__numero_serie',)


@admin.register(Entretien)
class EntretienAdmin(admin.ModelAdmin):
    list_display = ('moto', 'type_entretien', 'date_prevue', 'date_realisee')
    list_filter = ('type_entretien',)
    search_fields = ('moto__numero_serie',)
