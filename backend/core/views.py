from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Agence, JournalActivite, Utilisateur
from .permissions import IsAdmin, IsAdminOrGerant
from .serializers import AgenceSerializer, JournalActiviteSerializer, UtilisateurSerializer
from .utils import appliquer_periode, compter_donnees_commerciales, purger_donnees_commerciales


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


class JournalActiviteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = JournalActiviteSerializer
    permission_classes = [IsAuthenticated, IsAdminOrGerant]
    queryset = JournalActivite.objects.select_related('agence')

    def get_queryset(self):
        qs = self.queryset
        user = self.request.user
        if user.role != Utilisateur.Role.ADMIN:
            qs = qs.filter(agence=user.agence)
        else:
            agence_id = self.request.query_params.get('agence')
            if agence_id:
                qs = qs.filter(agence_id=agence_id)
        utilisateur = self.request.query_params.get('utilisateur')
        if utilisateur:
            qs = qs.filter(utilisateur_username__icontains=utilisateur)
        ressource = self.request.query_params.get('ressource')
        if ressource:
            qs = qs.filter(ressource=ressource)
        return appliquer_periode(qs, 'date_action__date', self.request)


class PurgeDonneesCommercialesView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response(compter_donnees_commerciales())

    def post(self, request):
        if request.data.get('confirmation') != 'SUPPRIMER':
            return Response({'detail': "Confirmation invalide."}, status=400)
        return Response(purger_donnees_commerciales())
