from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from caisse.models import Versement
from catalogue.models import Couleur, Fournisseur, Marque, TypeMoto
from core.models import Agence, Utilisateur
from depenses.models import CategorieDepense, Depense
from facturation.models import Client, Facture
from stock.models import Arrivage, Moto


class DashboardTestBase(APITestCase):
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
        self.admin = Utilisateur.objects.create_user(
            username='admin', password='pass12345', role=Utilisateur.Role.ADMIN,
        )

        self.fournisseur = Fournisseur.objects.create(nom='Moto Import SA')
        self.marque = Marque.objects.create(nom='Yamaha')
        self.type_moto = TypeMoto.objects.create(marque=self.marque, nom='XTZ 125', seuil_alerte=3)
        self.couleur = Couleur.objects.create(nom='Rouge')
        self.arrivage_a = Arrivage.objects.create(
            agence=self.agence_a, fournisseur=self.fournisseur, numero_bon='BON-A-001',
            date_arrivage='2026-01-10', cree_par=self.gerant_a,
        )
        self.moto_a = Moto.objects.create(
            numero_serie='SN-A-0001', type_moto=self.type_moto, couleur=self.couleur,
            arrivage=self.arrivage_a, agence=self.agence_a,
        )
        self.client_a = Client.objects.create(agence=self.agence_a, nom='Jean Client')

        self.client.force_authenticate(user=self.gerant_a)
        creation = self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [{'moto': self.moto_a.id, 'quantite': 1, 'prix_unitaire': '1000000'}],
        }, format='json')
        self.facture = Facture.objects.get(id=creation.data['id'])

        categorie_carburant, _ = CategorieDepense.objects.get_or_create(nom='Carburant')
        Depense.objects.create(
            agence=self.agence_a, categorie=categorie_carburant, montant='50000',
            date_depense=date.today().isoformat(), cree_par=self.gerant_a,
        )
        Versement.objects.create(
            facture=self.facture, agence=self.agence_a, montant='300000',
            mode_paiement=Versement.ModePaiement.ESPECES, cree_par=self.gerant_a,
        )


class DashboardKPIsTests(DashboardTestBase):
    def test_kpis_scope_agence(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.get(reverse('dashboard-kpis'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['ventes_du_jour']['nb_factures'], 1)
        self.assertEqual(response.data['ventes_du_jour']['total'], '1000000.00')
        self.assertEqual(response.data['stock_critique'], 1)
        self.assertEqual(response.data['tresorerie'], '250000.00')

    def test_vendeur_b_isolated_from_agence_a(self):
        self.client.force_authenticate(user=self.vendeur_b)
        response = self.client.get(reverse('dashboard-kpis'))
        self.assertEqual(response.data['ventes_du_jour']['nb_factures'], 0)
        self.assertEqual(response.data['tresorerie'], '0')

    def test_admin_filter_par_agence(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('dashboard-kpis'), {'agence': self.agence_a.id})
        self.assertEqual(response.data['ventes_du_jour']['nb_factures'], 1)


class RapportComparatifTests(DashboardTestBase):
    def test_comparatif_periode_contient_le_mois_courant(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.get(reverse('dashboard-comparatif-periode'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['total_ventes'], '1000000.00')
        self.assertEqual(response.data[0]['total_depenses'], '50000.00')

    def test_comparatif_agences_reserve_admin(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.get(reverse('dashboard-comparatif-agences'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_comparatif_agences_admin_voit_toutes_les_agences(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('dashboard-comparatif-agences'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        agence_a_row = next(r for r in response.data if r['agence'] == 'Agence A')
        self.assertEqual(agence_a_row['total_ventes'], '1000000.00')
        self.assertEqual(agence_a_row['tresorerie'], '250000.00')


class RapportMargeArrivagesTests(DashboardTestBase):
    def test_marge_arrivage_scope_agence(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.get(reverse('dashboard-marge-arrivages'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        row = response.data[0]
        self.assertEqual(row['numero_bon'], 'BON-A-001')
        self.assertEqual(row['nb_motos'], 1)
        self.assertEqual(row['total_revient'], '0.00')
        self.assertEqual(row['total_vente'], '1000000.00')
        self.assertEqual(row['total_marge'], '1000000.00')

    def test_vendeur_b_isolated_from_arrivage_a(self):
        self.client.force_authenticate(user=self.vendeur_b)
        response = self.client.get(reverse('dashboard-marge-arrivages'))
        self.assertEqual(response.data, [])
