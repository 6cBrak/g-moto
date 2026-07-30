from django.contrib import admin

from .models import Versement


@admin.register(Versement)
class VersementAdmin(admin.ModelAdmin):
    list_display = ('facture', 'montant', 'mode_paiement', 'agence', 'date_versement')
    list_filter = ('agence', 'mode_paiement')
    search_fields = ('facture__numero_facture',)
