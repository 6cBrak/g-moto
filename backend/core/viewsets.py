from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Utilisateur
from .permissions import IsAdminOrGerant


class AgenceScopedViewSet(viewsets.ModelViewSet):
    """ModelViewSet dont le queryset et la creation sont restreints a l'agence
    de l'utilisateur connecte (sauf pour un admin, qui voit/gere tout).
    Suppose que le modele expose un champ ou une relation 'agence'.
    """

    permission_classes = [IsAuthenticated]
    agence_lookup = 'agence'

    def get_queryset(self):
        user = self.request.user
        if user.role == Utilisateur.Role.ADMIN:
            qs = self.queryset
            agence_id = self.request.query_params.get('agence')
            if agence_id:
                qs = qs.filter(**{self.agence_lookup: agence_id})
            return qs
        return self.queryset.filter(**{self.agence_lookup: user.agence})

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAuthenticated(), IsAdminOrGerant()]
        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == Utilisateur.Role.ADMIN:
            serializer.save()
        else:
            serializer.save(agence=user.agence)
