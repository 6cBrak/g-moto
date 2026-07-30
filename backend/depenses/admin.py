from django.contrib import admin

from .models import Depense


@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    list_display = ('categorie', 'montant', 'agence', 'date_depense', 'cree_par')
    list_filter = ('agence', 'categorie')
    search_fields = ('description',)
