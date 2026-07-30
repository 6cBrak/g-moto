from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Agence, Utilisateur


class AuthTests(APITestCase):
    def setUp(self):
        self.agence = Agence.objects.create(nom='Agence Test')
        self.user = Utilisateur.objects.create_user(
            username='vendeur1', password='pass12345',
            role=Utilisateur.Role.VENDEUR_CAISSIER, agence=self.agence,
        )

    def test_login_returns_tokens(self):
        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': 'vendeur1', 'password': 'pass12345'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': 'vendeur1', 'password': 'wrong'},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_requires_authentication(self):
        response = self.client.get(reverse('me'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_current_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'vendeur1')
        self.assertEqual(response.data['agence_nom'], 'Agence Test')


class AgenceFilteringTests(APITestCase):
    def setUp(self):
        self.agence_a = Agence.objects.create(nom='Agence A')
        self.agence_b = Agence.objects.create(nom='Agence B')

        self.admin = Utilisateur.objects.create_user(
            username='admin', password='pass12345', role=Utilisateur.Role.ADMIN,
        )
        self.gerant_a = Utilisateur.objects.create_user(
            username='gerant_a', password='pass12345',
            role=Utilisateur.Role.GERANT, agence=self.agence_a,
        )
        self.vendeur_a = Utilisateur.objects.create_user(
            username='vendeur_a', password='pass12345',
            role=Utilisateur.Role.VENDEUR_CAISSIER, agence=self.agence_a,
        )
        self.vendeur_b = Utilisateur.objects.create_user(
            username='vendeur_b', password='pass12345',
            role=Utilisateur.Role.VENDEUR_CAISSIER, agence=self.agence_b,
        )

    def test_admin_sees_all_agences(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('agence-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_gerant_sees_only_own_agence(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.get(reverse('agence-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['nom'], 'Agence A')

    def test_gerant_sees_only_own_agence_users(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.get(reverse('utilisateur-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = {u['username'] for u in response.data['results']}
        self.assertEqual(usernames, {'gerant_a', 'vendeur_a'})

    def test_vendeur_cannot_list_utilisateurs(self):
        self.client.force_authenticate(user=self.vendeur_a)
        response = self.client.get(reverse('utilisateur-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_gerant_cannot_create_agence(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.post(reverse('agence-list'), {'nom': 'Agence C'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_gerant_creating_user_forces_own_agence_and_role(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.post(reverse('utilisateur-list'), {
            'username': 'nouveau',
            'password': 'pass12345',
            'agence': self.agence_b.id,
            'role': Utilisateur.Role.ADMIN,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Utilisateur.objects.get(username='nouveau')
        self.assertEqual(created.agence, self.agence_a)
        self.assertEqual(created.role, Utilisateur.Role.VENDEUR_CAISSIER)
