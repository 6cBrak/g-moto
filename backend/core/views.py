from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Agence, Utilisateur
from .permissions import IsAdmin, IsAdminOrGerant
from .serializers import AgenceSerializer, UtilisateurSerializer


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'agence': user.agence_id,
            'agence_nom': user.agence.nom if user.agence else None,
        })


class AgenceViewSet(viewsets.ModelViewSet):
    serializer_class = AgenceSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role == Utilisateur.Role.ADMIN:
            return Agence.objects.all()
        return Agence.objects.filter(id=user.agence_id)


class UtilisateurViewSet(viewsets.ModelViewSet):
    serializer_class = UtilisateurSerializer
    permission_classes = [IsAuthenticated, IsAdminOrGerant]

    def get_queryset(self):
        user = self.request.user
        if user.role == Utilisateur.Role.ADMIN:
            return Utilisateur.objects.all()
        return Utilisateur.objects.filter(agence=user.agence)

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == Utilisateur.Role.GERANT:
            serializer.save(agence=user.agence, role=Utilisateur.Role.VENDEUR_CAISSIER)
        else:
            serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        if user.role == Utilisateur.Role.GERANT:
            serializer.save(agence=user.agence)
        else:
            serializer.save()
