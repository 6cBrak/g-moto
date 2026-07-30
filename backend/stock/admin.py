from django.contrib import admin

from .models import Arrivage, HistoriqueMoto, Moto


@admin.register(Arrivage)
class ArrivageAdmin(admin.ModelAdmin):
    list_display = ('numero_bon', 'agence', 'fournisseur', 'date_arrivage')
    list_filter = ('agence', 'fournisseur')
    search_fields = ('numero_bon',)


@admin.register(Moto)
class MotoAdmin(admin.ModelAdmin):
    list_display = (
        'numero_serie', 'type_moto', 'couleur', 'agence', 'statut', 'immatriculation',
    )
    list_filter = ('agence', 'statut', 'type_moto__marque')
    search_fields = ('numero_serie', 'immatriculation')


@admin.register(HistoriqueMoto)
class HistoriqueMotoAdmin(admin.ModelAdmin):
    list_display = ('moto', 'type_evenement', 'agence_source', 'agence_destination', 'date_evenement')
    list_filter = ('type_evenement',)
    search_fields = ('moto__numero_serie',)
