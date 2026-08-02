from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalogue.models import Couleur, Fournisseur, Marque, TypeMoto
from core.models import Agence, Utilisateur
from stock.models import Arrivage, HistoriqueMoto, Moto

from .models import CarteGrise, Client, DepotVente, EnvoiDepot, Facture


class FacturationTestBase(APITestCase):
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
        self.client_a = Client.objects.create(agence=self.agence_a, nom='Jean Client')


class FactureCreationTests(FacturationTestBase):
    def test_creation_facture_avec_moto_marque_vendue_et_historique(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [
                {'moto': self.moto_a.id, 'quantite': 1, 'prix_unitaire': '1500000'},
            ],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        facture = Facture.objects.get(id=response.data['id'])
        self.assertEqual(facture.agence, self.agence_a)
        self.assertTrue(facture.numero_facture.startswith(f"F{self.agence_a.id:02d}-"))
        self.assertEqual(str(facture.total), '1500000.00')

        self.moto_a.refresh_from_db()
        self.assertEqual(self.moto_a.statut, Moto.Statut.VENDUE)

        event = self.moto_a.historique.filter(type_evenement=HistoriqueMoto.TypeEvenement.VENTE).first()
        self.assertIsNotNone(event)

    def test_numero_facture_sequence_incremente(self):
        self.client.force_authenticate(user=self.gerant_a)
        moto2 = Moto.objects.create(
            numero_serie='SN-A-0002', type_moto=self.type_moto, couleur=self.couleur,
            arrivage=self.arrivage_a, agence=self.agence_a,
        )
        r1 = self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [{'moto': self.moto_a.id, 'quantite': 1, 'prix_unitaire': '1000000'}],
        }, format='json')
        r2 = self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [{'moto': moto2.id, 'quantite': 1, 'prix_unitaire': '1000000'}],
        }, format='json')
        num1 = r1.data['numero_facture']
        num2 = r2.data['numero_facture']
        seq1 = int(num1.rsplit('-', 1)[-1])
        seq2 = int(num2.rsplit('-', 1)[-1])
        self.assertEqual(seq2, seq1 + 1)

    def test_cannot_sell_moto_not_en_stock(self):
        self.moto_a.statut = Moto.Statut.VENDUE
        self.moto_a.save()
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [{'moto': self.moto_a.id, 'quantite': 1, 'prix_unitaire': '1000000'}],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vendeur_b_cannot_see_facture_agence_a(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [{'moto': self.moto_a.id, 'quantite': 1, 'prix_unitaire': '1000000'}],
        }, format='json')
        facture_id = response.data['id']

        self.client.force_authenticate(user=self.vendeur_b)
        detail = self.client.get(reverse('facture-detail', args=[facture_id]))
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_facture_pdf_endpoint_returns_pdf(self):
        self.client.force_authenticate(user=self.gerant_a)
        creation = self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [{'moto': self.moto_a.id, 'quantite': 1, 'prix_unitaire': '1000000'}],
        }, format='json')
        facture_id = creation.data['id']

        response = self.client.get(reverse('facture-pdf', args=[facture_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_ligne_expose_fichier_cmc_de_larrivage(self):
        self.arrivage_a.fichier_cmc = SimpleUploadedFile('cmc.pdf', b'contenu', content_type='application/pdf')
        self.arrivage_a.save()

        self.client.force_authenticate(user=self.gerant_a)
        creation = self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [{'moto': self.moto_a.id, 'quantite': 1, 'prix_unitaire': '1000000'}],
        }, format='json')
        self.assertEqual(creation.status_code, status.HTTP_201_CREATED, creation.data)
        self.assertIsNotNone(creation.data['lignes'][0]['arrivage_fichier_cmc'])

    def test_ligne_sans_fichier_cmc_renvoie_null(self):
        self.client.force_authenticate(user=self.gerant_a)
        creation = self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [{'moto': self.moto_a.id, 'quantite': 1, 'prix_unitaire': '1000000'}],
        }, format='json')
        self.assertIsNone(creation.data['lignes'][0]['arrivage_fichier_cmc'])


class CarteGriseTests(FacturationTestBase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.gerant_a)
        creation = self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [{'moto': self.moto_a.id, 'quantite': 1, 'prix_unitaire': '1000000'}],
        }, format='json')
        self.facture = Facture.objects.get(id=creation.data['id'])

    def test_create_and_retirer_carte_grise(self):
        response = self.client.post(reverse('cartegrise-list'), {
            'facture': self.facture.id, 'numero_dossier': 'CG-001',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['retiree'])

        retrait = self.client.post(reverse('cartegrise-retirer', args=[response.data['id']]))
        self.assertEqual(retrait.status_code, status.HTTP_200_OK)
        self.assertTrue(retrait.data['retiree'])

    def test_filtrer_cartes_grises_par_facture(self):
        moto2 = Moto.objects.create(
            numero_serie='SN-A-0002', type_moto=self.type_moto, couleur=self.couleur,
            arrivage=self.arrivage_a, agence=self.agence_a,
        )
        autre_facture_resp = self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [{'moto': moto2.id, 'quantite': 1, 'prix_unitaire': '500000'}],
        }, format='json')
        CarteGrise.objects.create(facture_id=autre_facture_resp.data['id'], numero_dossier='CG-AUTRE')
        self.client.post(reverse('cartegrise-list'), {'facture': self.facture.id, 'numero_dossier': 'CG-001'})

        response = self.client.get(reverse('cartegrise-list'), {'facture': self.facture.id})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['numero_dossier'], 'CG-001')

    def test_vendeur_b_cannot_attach_carte_grise_to_other_agence_facture(self):
        self.client.force_authenticate(user=self.vendeur_b)
        response = self.client.post(reverse('cartegrise-list'), {
            'facture': self.facture.id, 'numero_dossier': 'CG-002',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recevoir_puis_retirer_avec_nom_et_telephone(self):
        creation = self.client.post(reverse('cartegrise-list'), {
            'facture': self.facture.id, 'numero_dossier': 'CG-003',
        })
        carte_id = creation.data['id']
        self.assertFalse(creation.data['recue'])

        reception = self.client.post(reverse('cartegrise-recevoir', args=[carte_id]))
        self.assertEqual(reception.status_code, status.HTTP_200_OK)
        self.assertTrue(reception.data['recue'])
        self.assertFalse(reception.data['retiree'])

        retrait = self.client.post(reverse('cartegrise-retirer', args=[carte_id]), {
            'retirer_nom': 'Awa Kone', 'retirer_telephone': '0102030405',
        })
        self.assertEqual(retrait.status_code, status.HTTP_200_OK)
        self.assertTrue(retrait.data['retiree'])
        self.assertEqual(retrait.data['retirer_nom'], 'Awa Kone')
        self.assertEqual(retrait.data['retirer_telephone'], '0102030405')
        self.assertIsNotNone(retrait.data['date_retrait'])


class ClientSegmentationTests(FacturationTestBase):
    def test_filtrer_clients_par_segment(self):
        Client.objects.create(agence=self.agence_a, nom='Revendeur Moto+', segment=Client.Segment.REVENDEUR)
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.get(reverse('client-list'), {'segment': Client.Segment.REVENDEUR})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['nom'], 'Revendeur Moto+')

    def test_marquer_client_vip(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.patch(reverse('client-detail', args=[self.client_a.id]), {
            'segment': Client.Segment.VIP,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client_a.refresh_from_db()
        self.assertEqual(self.client_a.segment, Client.Segment.VIP)


class ClientHistoriqueTests(FacturationTestBase):
    def test_historique_client_liste_les_factures(self):
        self.client.force_authenticate(user=self.gerant_a)
        self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [{'moto': self.moto_a.id, 'quantite': 1, 'prix_unitaire': '1000000'}],
        }, format='json')

        response = self.client.get(reverse('client-historique', args=[self.client_a.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['factures']), 1)
        self.assertEqual(response.data['factures'][0]['solde'], '1000000.00')


class DepotVenteTests(FacturationTestBase):
    def setUp(self):
        super().setUp()
        self.client_revendeur = Client.objects.create(
            agence=self.agence_a, nom='Revendeur Moto+', segment=Client.Segment.REVENDEUR,
        )
        self.moto_b = Moto.objects.create(
            numero_serie='SN-A-0002', type_moto=self.type_moto, couleur=self.couleur,
            arrivage=self.arrivage_a, agence=self.agence_a,
        )

    def test_envoyer_en_depot_change_statut_motos(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.post(reverse('envoidepot-list'), {
            'client': self.client_revendeur.id,
            'motos': [self.moto_a.id, self.moto_b.id],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(len(response.data['lignes']), 2)

        self.moto_a.refresh_from_db()
        self.moto_b.refresh_from_db()
        self.assertEqual(self.moto_a.statut, Moto.Statut.EN_DEPOT)
        self.assertEqual(self.moto_b.statut, Moto.Statut.EN_DEPOT)
        self.assertTrue(
            self.moto_a.historique.filter(type_evenement=HistoriqueMoto.TypeEvenement.DEPOT).exists(),
        )

    def test_cannot_envoyer_moto_deja_vendue(self):
        self.moto_a.statut = Moto.Statut.VENDUE
        self.moto_a.save()
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.post(reverse('envoidepot-list'), {
            'client': self.client_revendeur.id,
            'motos': [self.moto_a.id],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retour_depot_remet_en_stock(self):
        self.client.force_authenticate(user=self.gerant_a)
        envoi = self.client.post(reverse('envoidepot-list'), {
            'client': self.client_revendeur.id,
            'motos': [self.moto_a.id],
        }, format='json')
        ligne_id = envoi.data['lignes'][0]['id']

        retour = self.client.post(reverse('depotvente-retourner', args=[ligne_id]))
        self.assertEqual(retour.status_code, status.HTTP_200_OK)
        self.assertEqual(retour.data['statut'], DepotVente.Statut.RETOURNEE)

        self.moto_a.refresh_from_db()
        self.assertEqual(self.moto_a.statut, Moto.Statut.EN_STOCK)
        self.assertTrue(
            self.moto_a.historique.filter(type_evenement=HistoriqueMoto.TypeEvenement.RETOUR_DEPOT).exists(),
        )

    def test_vente_moto_en_depot_resout_le_depot(self):
        self.client.force_authenticate(user=self.gerant_a)
        self.client.post(reverse('envoidepot-list'), {
            'client': self.client_revendeur.id,
            'motos': [self.moto_a.id],
        }, format='json')

        facture = self.client.post(reverse('facture-list'), {
            'client': self.client_revendeur.id,
            'lignes': [{'moto': self.moto_a.id, 'quantite': 1, 'prix_unitaire': '900000'}],
        }, format='json')
        self.assertEqual(facture.status_code, status.HTTP_201_CREATED, facture.data)

        self.moto_a.refresh_from_db()
        self.assertEqual(self.moto_a.statut, Moto.Statut.VENDUE)
        depot_ligne = DepotVente.objects.get(moto=self.moto_a)
        self.assertEqual(depot_ligne.statut, DepotVente.Statut.VENDUE)
        self.assertEqual(depot_ligne.ligne_facture.facture_id, facture.data['id'])

    def test_cannot_facturer_moto_en_depot_chez_autre_client(self):
        self.client.force_authenticate(user=self.gerant_a)
        self.client.post(reverse('envoidepot-list'), {
            'client': self.client_revendeur.id,
            'motos': [self.moto_a.id],
        }, format='json')

        facture = self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [{'moto': self.moto_a.id, 'quantite': 1, 'prix_unitaire': '900000'}],
        }, format='json')
        self.assertEqual(facture.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bon_depot_pdf(self):
        self.client.force_authenticate(user=self.gerant_a)
        envoi = self.client.post(reverse('envoidepot-list'), {
            'client': self.client_revendeur.id,
            'motos': [self.moto_a.id],
        }, format='json')
        response = self.client.get(reverse('envoidepot-pdf', args=[envoi.data['id']]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_client_depots_en_cours(self):
        self.client.force_authenticate(user=self.gerant_a)
        self.client.post(reverse('envoidepot-list'), {
            'client': self.client_revendeur.id,
            'motos': [self.moto_a.id, self.moto_b.id],
        }, format='json')
        response = self.client.get(reverse('client-depots-en-cours', args=[self.client_revendeur.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class ClientRelancesTests(FacturationTestBase):
    def test_carte_grise_ancienne_apparait_en_relance(self):
        self.client.force_authenticate(user=self.gerant_a)
        creation = self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [{'moto': self.moto_a.id, 'quantite': 1, 'prix_unitaire': '1000000'}],
        }, format='json')
        facture = Facture.objects.get(id=creation.data['id'])
        carte_grise = CarteGrise.objects.create(facture=facture, numero_dossier='CG-001')
        # Simule une soumission ancienne (au-dela du seuil de relance).
        CarteGrise.objects.filter(id=carte_grise.id).update(date_soumission='2020-01-01')

        response = self.client.get(reverse('client-relances'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['type'], 'carte_grise')

    def test_carte_grise_recente_n_apparait_pas(self):
        self.client.force_authenticate(user=self.gerant_a)
        creation = self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [{'moto': self.moto_a.id, 'quantite': 1, 'prix_unitaire': '1000000'}],
        }, format='json')
        facture = Facture.objects.get(id=creation.data['id'])
        CarteGrise.objects.create(facture=facture, numero_dossier='CG-002')

        response = self.client.get(reverse('client-relances'))
        self.assertEqual(len(response.data), 0)
