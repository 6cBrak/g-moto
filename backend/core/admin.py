from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Agence, Utilisateur


@admin.register(Agence)
class AgenceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'telephone', 'actif', 'date_creation')
    search_fields = ('nom',)


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Gestion moto', {'fields': ('role', 'agence')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Gestion moto', {'fields': ('role', 'agence')}),
    )
    list_display = ('username', 'email', 'role', 'agence', 'is_staff')
    list_filter = ('role', 'agence', 'is_staff', 'is_active')
