from django.contrib import admin

from .models import Couleur, Fournisseur, Marque, ModeleCasque, TypeMoto


@admin.register(Marque)
class MarqueAdmin(admin.ModelAdmin):
    list_display = ('nom', 'actif')
    search_fields = ('nom',)


@admin.register(Couleur)
class CouleurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code_hex')
    search_fields = ('nom',)


@admin.register(TypeMoto)
class TypeMotoAdmin(admin.ModelAdmin):
    list_display = ('marque', 'nom', 'code', 'cylindree', 'actif')
    list_filter = ('marque',)
    search_fields = ('nom',)


@admin.register(ModeleCasque)
class ModeleCasqueAdmin(admin.ModelAdmin):
    list_display = ('nom', 'taille', 'actif')
    search_fields = ('nom',)


@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'contact', 'telephone', 'actif')
    search_fields = ('nom',)
