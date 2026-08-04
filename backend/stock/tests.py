from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalogue.models import Couleur, Fournisseur, Marque, TypeMoto
from core.models import Agence, Utilisateur

from .models import Arrivage, HistoriqueMoto, Moto


class StockTestBase(APITestCase):
    def setUp(self):
        self.agence_a = Agence.objects.create(nom='Agence A')
        self.agence_b = Agence.objects.create(nom='Agence B')

        self.admin = Utilisateur.objects.create_user(
            username='admin', password='pass12345', role=Utilisateur.Role.ADMIN,
        )
        self.vendeur_a = Utilisateur.objects.create_user(
            username='vendeur_a', password='pass12345',
            role=Utilisateur.Role.VENDEUR_CAISSIER, agence=self.agence_a,
        )
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
        self.arrivage_b = Arrivage.objects.create(
            agence=self.agence_b, fournisseur=self.fournisseur, numero_bon='BON-B-001',
            date_arrivage='2026-01-11', cree_par=self.vendeur_b,
        )

        self.moto_a = Moto.objects.create(
            numero_serie='SN-A-0001', type_moto=self.type_moto, couleur=self.couleur,
            arrivage=self.arrivage_a, agence=self.agence_a,
        )
        self.moto_b = Moto.objects.create(
            numero_serie='SN-B-0001', type_moto=self.type_moto, couleur=self.couleur,
            arrivage=self.arrivage_b, agence=self.agence_b,
        )


class ArrivageTests(StockTestBase):
    def test_vendeur_sees_only_own_agence_arrivages(self):
        self.client.force_authenticate(user=self.vendeur_a)
        response = self.client.get(reverse('arrivage-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['numero_bon'], 'BON-A-001')

    def test_admin_sees_all_arrivages(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('arrivage-list'))
        self.assertEqual(response.data['count'], 2)

    def test_vendeur_create_forces_own_agence(self):
        self.client.force_authenticate(user=self.vendeur_a)
        response = self.client.post(reverse('arrivage-list'), {
            'agence': self.agence_b.id,
            'fournisseur': self.fournisseur.id,
            'numero_bon': 'BON-A-002',
            'date_arrivage': '2026-02-01',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        arrivage = Arrivage.objects.get(numero_bon='BON-A-002')
        self.assertEqual(arrivage.agence, self.agence_a)
        self.assertEqual(arrivage.cree_par, self.vendeur_a)

    def test_vendeur_cannot_delete_arrivage(self):
        self.client.force_authenticate(user=self.vendeur_a)
        response = self.client.delete(reverse('arrivage-detail', args=[self.arrivage_a.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_arrivage_pdf_endpoint_returns_pdf(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.get(reverse('arrivage-pdf', args=[self.arrivage_a.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')


class MotoTests(StockTestBase):
    def test_numero_serie_must_be_unique(self):
        with self.assertRaises(Exception):
            Moto.objects.create(
                numero_serie='SN-A-0001', type_moto=self.type_moto, couleur=self.couleur,
                arrivage=self.arrivage_a, agence=self.agence_a,
            )

    def test_vendeur_sees_only_own_agence_motos(self):
        self.client.force_authenticate(user=self.vendeur_a)
        response = self.client.get(reverse('moto-list'))
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['numero_serie'], 'SN-A-0001')

    def test_creating_moto_logs_historique_arrivage(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.post(reverse('moto-list'), {
            'numero_serie': 'SN-A-0002', 'type_moto': self.type_moto.id,
            'couleur': self.couleur.id, 'arrivage': self.arrivage_a.id,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        moto = Moto.objects.get(numero_serie='SN-A-0002')
        events = moto.historique.all()
        self.assertEqual(events.count(), 1)
        self.assertEqual(events[0].type_evenement, HistoriqueMoto.TypeEvenement.ARRIVAGE)

    def test_vendeur_cannot_transfer_moto(self):
        self.client.force_authenticate(user=self.vendeur_a)
        response = self.client.post(
            reverse('moto-transferer', args=[self.moto_a.id]),
            {'agence_destination': self.agence_b.id},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_gerant_transfer_moto_changes_agence_and_logs_history(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.post(
            reverse('moto-transferer', args=[self.moto_a.id]),
            {'agence_destination': self.agence_b.id, 'commentaire': 'reequilibrage stock'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.moto_a.refresh_from_db()
        self.assertEqual(self.moto_a.agence, self.agence_b)

        event = self.moto_a.historique.filter(
            type_evenement=HistoriqueMoto.TypeEvenement.TRANSFERT,
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.agence_source, self.agence_a)
        self.assertEqual(event.agence_destination, self.agence_b)

    def test_peut_modifier_moto_en_stock(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.patch(
            reverse('moto-detail', args=[self.moto_a.id]), {'immatriculation': 'AB-1234-CD'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.moto_a.refresh_from_db()
        self.assertEqual(self.moto_a.immatriculation, 'AB-1234-CD')

    def test_peut_supprimer_moto_en_stock(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.delete(reverse('moto-detail', args=[self.moto_a.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Moto.objects.filter(id=self.moto_a.id).exists())

    def test_cannot_modifier_moto_vendue(self):
        self.moto_a.statut = Moto.Statut.VENDUE
        self.moto_a.save()
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.patch(
            reverse('moto-detail', args=[self.moto_a.id]), {'immatriculation': 'AB-1234-CD'},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_supprimer_moto_vendue(self):
        self.moto_a.statut = Moto.Statut.VENDUE
        self.moto_a.save()
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.delete(reverse('moto-detail', args=[self.moto_a.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Moto.objects.filter(id=self.moto_a.id).exists())

    def test_historique_endpoint_lists_events(self):
        self.client.force_authenticate(user=self.gerant_a)
        self.client.post(
            reverse('moto-transferer', args=[self.moto_a.id]),
            {'agence_destination': self.agence_b.id},
        )
        # Une fois transferee hors de son agence, seul l'admin (vue consolidee) y accede encore.
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('moto-historique', args=[self.moto_a.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['type_evenement'], 'transfert')


class StockVueEnsembleTests(StockTestBase):
    def test_vue_ensemble_scope_agence(self):
        self.client.force_authenticate(user=self.vendeur_a)
        response = self.client.get(reverse('stock-vue-ensemble'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_en_stock'], 1)
        self.assertEqual(response.data['par_agence'][0]['agence__nom'], 'Agence A')

    def test_vue_ensemble_admin_consolide_toutes_agences(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('stock-vue-ensemble'))
        self.assertEqual(response.data['total_en_stock'], 2)

    def test_vue_ensemble_expose_valeur_totale(self):
        self.moto_a.prix_achat = '850000'
        self.moto_a.save()
        self.client.force_authenticate(user=self.vendeur_a)
        response = self.client.get(reverse('stock-vue-ensemble'))
        self.assertEqual(response.data['valeur_totale'], Decimal('850000.00'))
        self.assertEqual(response.data['par_agence'][0]['valeur'], Decimal('850000.00'))
        self.assertEqual(response.data['par_type'][0]['valeur'], Decimal('850000.00'))

    def test_vue_ensemble_valeur_totale_nulle_sans_prix_achat(self):
        self.client.force_authenticate(user=self.vendeur_a)
        response = self.client.get(reverse('stock-vue-ensemble'))
        self.assertEqual(response.data['valeur_totale'], Decimal('0'))

    def test_alerte_stock_bas_declenchee_sous_le_seuil(self):
        # seuil_alerte par defaut = 3, seule 1 moto en stock pour ce type dans l'agence A
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.get(reverse('stock-alertes'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['quantite_stock'], 1)
        self.assertEqual(response.data[0]['seuil_alerte'], 3)

    def test_pas_d_alerte_si_stock_suffisant(self):
        self.type_moto.seuil_alerte = 1
        self.type_moto.save()
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.get(reverse('stock-alertes'))
        self.assertEqual(len(response.data), 0)

    def test_alerte_pas_dupliquee_avec_plusieurs_motos_du_meme_type(self):
        # Plusieurs motos du meme type/agence (toujours sous le seuil de 3) ne doivent
        # produire qu'UNE seule ligne d'alerte, pas une par moto.
        Moto.objects.create(
            numero_serie='SN-A-0002', type_moto=self.type_moto, couleur=self.couleur,
            arrivage=self.arrivage_a, agence=self.agence_a,
        )
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.get(reverse('stock-alertes'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['quantite_stock'], 2)
