from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Agence, Utilisateur

from .models import Marque


class CatalogueTests(APITestCase):
    def setUp(self):
        self.agence = Agence.objects.create(nom='Agence Test')
        self.vendeur = Utilisateur.objects.create_user(
            username='vendeur1', password='pass12345',
            role=Utilisateur.Role.VENDEUR_CAISSIER, agence=self.agence,
        )
        self.gerant = Utilisateur.objects.create_user(
            username='gerant1', password='pass12345',
            role=Utilisateur.Role.GERANT, agence=self.agence,
        )
        self.marque = Marque.objects.create(nom='Yamaha')

    def test_vendeur_can_read_marques(self):
        self.client.force_authenticate(user=self.vendeur)
        response = self.client.get(reverse('marque-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_vendeur_cannot_create_marque(self):
        self.client.force_authenticate(user=self.vendeur)
        response = self.client.post(reverse('marque-list'), {'nom': 'Honda'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_gerant_can_create_marque(self):
        self.client.force_authenticate(user=self.gerant)
        response = self.client.post(reverse('marque-list'), {'nom': 'Honda'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_type_moto_requires_marque(self):
        self.client.force_authenticate(user=self.gerant)
        response = self.client.post(reverse('typemoto-list'), {
            'marque': self.marque.id, 'nom': 'XTZ 125', 'cylindree': 125,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['marque_nom'], 'Yamaha')

    def test_anonymous_cannot_access_catalogue(self):
        response = self.client.get(reverse('marque-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
