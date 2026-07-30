from rest_framework.permissions import BasePermission

from .models import Utilisateur


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == Utilisateur.Role.ADMIN)


class IsAdminOrGerant(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.role in (Utilisateur.Role.ADMIN, Utilisateur.Role.GERANT)
        )
