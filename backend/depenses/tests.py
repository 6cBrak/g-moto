from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from caisse.models import SessionCaisse
from core.models import Agence, Utilisateur

from .models import Depense


class DepenseTests(APITestCase):
    def setUp(self):
        self.agence_a = Agence.objects.create(nom='Agence A')
        self.agence_b = Agence.objects.create(nom='Agence B')
        self.vendeur_a = Utilisateur.objects.create_user(
            username='vendeur_a', password='pass12345',
            role=Utilisateur.Role.VENDEUR_CAISSIER, agence=self.agence_a,
        )
        SessionCaisse.objects.create(
            agence=self.agence_a, date_session=date.today(),
            montant_ouverture='0', ouvert_par=self.vendeur_a,
        )
        Depense.objects.create(
            agence=self.agence_a, categorie=Depense.Categorie.CARBURANT, montant='15000',
            date_depense='2026-01-05', cree_par=self.vendeur_a,
        )
        Depense.objects.create(
            agence=self.agence_b, categorie=Depense.Categorie.LOYER, montant='200000',
            date_depense='2026-01-05', cree_par=self.vendeur_a,
        )

    def test_vendeur_sees_only_own_agence_depenses(self):
        self.client.force_authenticate(user=self.vendeur_a)
        response = self.client.get(reverse('depense-list'))
        self.assertEqual(response.data['count'], 1)

    def test_create_depense_forces_own_agence(self):
        self.client.force_authenticate(user=self.vendeur_a)
        response = self.client.post(reverse('depense-list'), {
            'agence': self.agence_b.id,
            'categorie': Depense.Categorie.FOURNITURE,
            'montant': '5000',
            'date_depense': '2026-01-06',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        depense = Depense.objects.get(id=response.data['id'])
        self.assertEqual(depense.agence, self.agence_a)
