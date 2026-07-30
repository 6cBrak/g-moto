from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalogue.models import Couleur, Fournisseur, Marque, TypeMoto
from core.models import Agence, Utilisateur
from stock.models import Arrivage, Moto

from .models import Entretien, Garantie


class ApresVenteTestBase(APITestCase):
    def setUp(self):
        self.agence_a = Agence.objects.create(nom='Agence A')
        self.agence_b = Agence.objects.create(nom='Agence B')

        self.gerant_a = Utilisateur.objects.create_user(
            username='gerant_a', password='pass12345',
            role=Utilisateur.Role.GERANT, agence=self.agence_a,
        )
        self.vendeur_b = Utilisateur.objects.create_user(
            username='vendeur_b', password='pass12345',
            role=Utilisateur.Role.VENDEUR_CAISSIER, agence=self.agence_b,
        )

        self.fournisseur = Fournisseur.objects.create(nom='Moto Import SA')
        self.marque = Marque.objects.create(nom='Yamaha')
        self.type_moto = TypeMoto.objects.create(marque=self.marque, nom='XTZ 125')
        self.couleur = Couleur.objects.create(nom='Rouge')
        self.arrivage_a = Arrivage.objects.create(
            agence=self.agence_a, fournisseur=self.fournisseur, numero_bon='BON-A-001',
            date_arrivage='2026-01-10', cree_par=self.gerant_a,
        )
        self.moto_a = Moto.objects.create(
            numero_serie='SN-A-0001', type_moto=self.type_moto, couleur=self.couleur,
            arrivage=self.arrivage_a, agence=self.agence_a,
        )


class GarantieTests(ApresVenteTestBase):
    def test_creer_garantie_calcule_date_fin(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.post(reverse('garantie-list'), {
            'moto': self.moto_a.id, 'date_debut': '2026-01-15', 'duree_mois': 12,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['date_fin'], '2027-01-15')
        self.assertTrue(response.data['active'])

    def test_vendeur_b_cannot_creer_garantie_autre_agence(self):
        self.client.force_authenticate(user=self.vendeur_b)
        response = self.client.post(reverse('garantie-list'), {
            'moto': self.moto_a.id, 'date_debut': '2026-01-15', 'duree_mois': 12,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_garantie_expiree(self):
        garantie = Garantie.objects.create(
            moto=self.moto_a, date_debut=date(2020, 1, 1), duree_mois=12, cree_par=self.gerant_a,
        )
        self.assertFalse(garantie.active)


class EntretienTests(ApresVenteTestBase):
    def test_creer_et_realiser_entretien(self):
        self.client.force_authenticate(user=self.gerant_a)
        creation = self.client.post(reverse('entretien-list'), {
            'moto': self.moto_a.id, 'type_entretien': Entretien.TypeEntretien.VIDANGE,
            'date_prevue': (date.today() + timedelta(days=10)).isoformat(),
        })
        self.assertEqual(creation.status_code, status.HTTP_201_CREATED)
        self.assertFalse(creation.data['realise'])

        realisation = self.client.post(reverse('entretien-realiser', args=[creation.data['id']]))
        self.assertEqual(realisation.status_code, status.HTTP_200_OK)
        self.assertTrue(realisation.data['realise'])

    def test_entretiens_a_venir_scope_agence(self):
        Entretien.objects.create(
            moto=self.moto_a, type_entretien=Entretien.TypeEntretien.CONTROLE,
            date_prevue=date.today() + timedelta(days=5), cree_par=self.gerant_a,
        )
        Entretien.objects.create(
            moto=self.moto_a, type_entretien=Entretien.TypeEntretien.REVISION_GENERALE,
            date_prevue=date.today() + timedelta(days=60), cree_par=self.gerant_a,
        )
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.get(reverse('entretiens-a-venir'), {'jours': 30})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_vendeur_b_ne_voit_pas_entretiens_agence_a(self):
        Entretien.objects.create(
            moto=self.moto_a, type_entretien=Entretien.TypeEntretien.CONTROLE,
            date_prevue=date.today() + timedelta(days=5), cree_par=self.gerant_a,
        )
        self.client.force_authenticate(user=self.vendeur_b)
        response = self.client.get(reverse('entretien-list'))
        self.assertEqual(response.data['count'], 0)
