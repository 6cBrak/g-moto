from django.contrib import admin

from .models import CarteGrise, Client, Declaration, Facture, LigneFacture, Quittance


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'agence', 'telephone', 'email')
    list_filter = ('agence',)
    search_fields = ('nom', 'telephone')


class LigneFactureInline(admin.TabularInline):
    model = LigneFacture
    extra = 0


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('numero_facture', 'agence', 'client', 'statut', 'date_facture', 'remarque')
    list_filter = ('agence', 'statut')
    search_fields = ('numero_facture',)
    inlines = [LigneFactureInline]


@admin.register(Declaration)
class DeclarationAdmin(admin.ModelAdmin):
    list_display = ('facture', 'numero_declaration', 'date_declaration')


@admin.register(CarteGrise)
class CarteGriseAdmin(admin.ModelAdmin):
    list_display = ('ligne_facture', 'numero_dossier', 'date_soumission', 'date_retrait')
    list_filter = ('date_retrait',)


@admin.register(Quittance)
class QuittanceAdmin(admin.ModelAdmin):
    list_display = ('facture', 'type_document', 'date_soumission', 'date_retrait')
    list_filter = ('type_document',)
