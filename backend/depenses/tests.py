from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from caisse.models import SessionCaisse
from core.models import Agence, Utilisateur

from .models import CategorieDepense, Depense


class DepenseTests(APITestCase):
    def setUp(self):
        self.agence_a = Agence.objects.create(nom='Agence A')
        self.agence_b = Agence.objects.create(nom='Agence B')
        self.vendeur_a = Utilisateur.objects.create_user(
            username='vendeur_a', password='pass12345',
            role=Utilisateur.Role.VENDEUR_CAISSIER, agence=self.agence_a,
        )
        self.categorie_carburant, _ = CategorieDepense.objects.get_or_create(nom='Carburant')
        self.categorie_loyer, _ = CategorieDepense.objects.get_or_create(nom='Loyer')
        self.categorie_fourniture, _ = CategorieDepense.objects.get_or_create(nom='Fourniture')

        SessionCaisse.objects.create(
            agence=self.agence_a, date_session=date.today(),
            montant_ouverture='1000000', ouvert_par=self.vendeur_a,
        )
        Depense.objects.create(
            agence=self.agence_a, categorie=self.categorie_carburant, montant='15000',
            date_depense='2026-01-05', cree_par=self.vendeur_a,
        )
        Depense.objects.create(
            agence=self.agence_b, categorie=self.categorie_loyer, montant='200000',
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
            'categorie': self.categorie_fourniture.id,
            'montant': '5000',
            'date_depense': '2026-01-06',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        depense = Depense.objects.get(id=response.data['id'])
        self.assertEqual(depense.agence, self.agence_a)

    def test_depense_bloquee_si_solde_insuffisant(self):
        SessionCaisse.objects.filter(agence=self.agence_a).update(montant_ouverture='1000')
        self.client.force_authenticate(user=self.vendeur_a)
        response = self.client.post(reverse('depense-list'), {
            'categorie': self.categorie_fourniture.id,
            'montant': '5000',
            'date_depense': '2026-01-06',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CategorieDepenseTests(APITestCase):
    def setUp(self):
        self.agence_a = Agence.objects.create(nom='Agence A')
        self.gerant_a = Utilisateur.objects.create_user(
            username='gerant_a', password='pass12345',
            role=Utilisateur.Role.GERANT, agence=self.agence_a,
        )
        self.vendeur_a = Utilisateur.objects.create_user(
            username='vendeur_a', password='pass12345',
            role=Utilisateur.Role.VENDEUR_CAISSIER, agence=self.agence_a,
        )

    def test_gerant_peut_creer_une_categorie(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.post(reverse('categoriedepense-list'), {'nom': 'Internet'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CategorieDepense.objects.filter(nom='Internet').exists())

    def test_vendeur_ne_peut_pas_creer_une_categorie(self):
        self.client.force_authenticate(user=self.vendeur_a)
        response = self.client.post(reverse('categoriedepense-list'), {'nom': 'Internet'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_vendeur_peut_lister_les_categories(self):
        CategorieDepense.objects.create(nom='Internet')
        self.client.force_authenticate(user=self.vendeur_a)
        response = self.client.get(reverse('categoriedepense-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        noms = [c['nom'] for c in response.data['results']]
        self.assertIn('Internet', noms)

    def test_gerant_peut_modifier_une_categorie(self):
        categorie = CategorieDepense.objects.create(nom='Internet')
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.patch(
            reverse('categoriedepense-detail', args=[categorie.id]), {'actif': False},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        categorie.refresh_from_db()
        self.assertFalse(categorie.actif)
