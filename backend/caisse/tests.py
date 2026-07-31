from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalogue.models import Couleur, Fournisseur, Marque, TypeMoto
from core.models import Agence, Utilisateur
from depenses.models import Depense
from facturation.models import Client, Facture
from stock.models import Arrivage, Moto

from .models import SessionCaisse, Versement


class CaisseTestBase(APITestCase):
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

        self.client.force_authenticate(user=self.gerant_a)
        creation = self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [{'moto': self.moto_a.id, 'quantite': 1, 'prix_unitaire': '1000000'}],
        }, format='json')
        self.facture = Facture.objects.get(id=creation.data['id'])

        Depense.objects.create(
            agence=self.agence_a, categorie=Depense.Categorie.CARBURANT, montant='20000',
            date_depense='2026-01-15', cree_par=self.gerant_a,
        )

        from datetime import date
        SessionCaisse.objects.create(
            agence=self.agence_a, date_session=date.today(),
            montant_ouverture='0', ouvert_par=self.gerant_a,
        )
        SessionCaisse.objects.create(
            agence=self.agence_b, date_session=date.today(),
            montant_ouverture='0', ouvert_par=self.vendeur_b,
        )


class VersementTests(CaisseTestBase):
    def test_create_versement_espece(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.post(reverse('versement-list'), {
            'facture': self.facture.id, 'montant': '400000',
            'mode_paiement': Versement.ModePaiement.ESPECES,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        versement = Versement.objects.get(id=response.data['id'])
        self.assertEqual(versement.agence, self.agence_a)

    def test_recu_versement_pdf(self):
        self.client.force_authenticate(user=self.gerant_a)
        creation = self.client.post(reverse('versement-list'), {
            'facture': self.facture.id, 'montant': '400000',
            'mode_paiement': Versement.ModePaiement.ESPECES,
        })
        response = self.client.get(reverse('versement-recu', args=[creation.data['id']]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_versement_ne_peut_pas_depasser_le_total_facture(self):
        self.client.force_authenticate(user=self.gerant_a)
        solde = self.client.post(reverse('versement-list'), {
            'facture': self.facture.id, 'montant': '1000000',
            'mode_paiement': Versement.ModePaiement.ESPECES,
        })
        self.assertEqual(solde.status_code, status.HTTP_201_CREATED)

        depassement = self.client.post(reverse('versement-list'), {
            'facture': self.facture.id, 'montant': '1',
            'mode_paiement': Versement.ModePaiement.ESPECES,
        })
        self.assertEqual(depassement.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtrer_versements_par_facture(self):
        moto2 = Moto.objects.create(
            numero_serie='SN-A-0002', type_moto=self.type_moto, couleur=self.couleur,
            arrivage=self.arrivage_a, agence=self.agence_a,
        )
        self.client.force_authenticate(user=self.gerant_a)
        autre_facture_resp = self.client.post(reverse('facture-list'), {
            'client': self.client_a.id,
            'lignes': [{'moto': moto2.id, 'quantite': 1, 'prix_unitaire': '500000'}],
        }, format='json')
        autre_facture_id = autre_facture_resp.data['id']

        Versement.objects.create(
            facture_id=autre_facture_id, agence=self.agence_a, montant='500000',
            mode_paiement=Versement.ModePaiement.ESPECES, cree_par=self.gerant_a,
        )
        self.client.post(reverse('versement-list'), {
            'facture': self.facture.id, 'montant': '400000',
            'mode_paiement': Versement.ModePaiement.ESPECES,
        })

        response = self.client.get(reverse('versement-list'), {'facture': self.facture.id})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['facture'], self.facture.id)

    def test_vendeur_cannot_verser_pour_facture_autre_agence(self):
        self.client.force_authenticate(user=self.vendeur_b)
        response = self.client.post(reverse('versement-list'), {
            'facture': self.facture.id, 'montant': '100000',
            'mode_paiement': Versement.ModePaiement.ORANGE_MONEY,
            'reference_transaction': 'OM-123456',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RapportsTests(CaisseTestBase):
    def test_rapport_ventes_scope_agence(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.get(reverse('caisse-rapport-ventes'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nb_factures'], 1)
        self.assertEqual(response.data['total_ventes'], '1000000.00')

    def test_rapport_depenses_par_categorie(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.get(reverse('caisse-rapport-depenses'))
        self.assertEqual(response.data['total_depenses'], '20000.00')
        self.assertEqual(response.data['par_categorie'][0]['categorie'], Depense.Categorie.CARBURANT)

    def test_clients_debiteurs_sans_versement(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.get(reverse('caisse-clients-debiteurs'))
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['solde'], '1000000.00')

    def test_clients_debiteurs_apres_versement_total(self):
        self.client.force_authenticate(user=self.gerant_a)
        self.client.post(reverse('versement-list'), {
            'facture': self.facture.id, 'montant': '1000000',
            'mode_paiement': Versement.ModePaiement.ESPECES,
        })
        response = self.client.get(reverse('caisse-clients-debiteurs'))
        self.assertEqual(len(response.data), 0)

    def test_journal_caisse_combine_versements_et_depenses(self):
        self.client.force_authenticate(user=self.gerant_a)
        self.client.post(reverse('versement-list'), {
            'facture': self.facture.id, 'montant': '300000',
            'mode_paiement': Versement.ModePaiement.WAVE,
        })
        response = self.client.get(reverse('caisse-journal'))
        types = {m['type'] for m in response.data}
        self.assertEqual(types, {'encaissement', 'decaissement'})

    def test_vendeur_b_scope_isolated_from_agence_a(self):
        self.client.force_authenticate(user=self.vendeur_b)
        response = self.client.get(reverse('caisse-rapport-ventes'))
        self.assertEqual(response.data['nb_factures'], 0)

    def test_historique_serie(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.get(reverse('caisse-historique-serie'), {'numero_serie': 'SN-A-0001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['moto']['numero_serie'], 'SN-A-0001')

    def test_admin_can_filter_by_agence_param(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('caisse-rapport-ventes'), {'agence': self.agence_b.id})
        self.assertEqual(response.data['nb_factures'], 0)


class SessionCaisseTests(CaisseTestBase):
    def test_versement_bloque_sans_session_ouverte(self):
        SessionCaisse.objects.filter(agence=self.agence_a).delete()
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.post(reverse('versement-list'), {
            'facture': self.facture.id, 'montant': '100000',
            'mode_paiement': Versement.ModePaiement.ESPECES,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ouvrir_puis_verser_fonctionne(self):
        SessionCaisse.objects.filter(agence=self.agence_a).delete()
        self.client.force_authenticate(user=self.gerant_a)
        ouverture = self.client.post(reverse('session-caisse-ouvrir'), {'montant_ouverture': '50000'})
        self.assertEqual(ouverture.status_code, status.HTTP_201_CREATED)

        response = self.client.post(reverse('versement-list'), {
            'facture': self.facture.id, 'montant': '100000',
            'mode_paiement': Versement.ModePaiement.ESPECES,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_ouverture_double_refusee(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.post(reverse('session-caisse-ouvrir'), {'montant_ouverture': '50000'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fermeture_calcule_ecart(self):
        self.client.force_authenticate(user=self.gerant_a)
        session = SessionCaisse.objects.get(agence=self.agence_a)
        self.client.post(reverse('versement-list'), {
            'facture': self.facture.id, 'montant': '100000',
            'mode_paiement': Versement.ModePaiement.ESPECES,
        })
        fermeture = self.client.post(
            reverse('session-caisse-fermer', args=[session.id]), {'montant_fermeture': '90000'},
        )
        self.assertEqual(fermeture.status_code, status.HTTP_200_OK)
        self.assertEqual(fermeture.data['montant_theorique'], '100000.00')
        self.assertEqual(fermeture.data['ecart'], '-10000.00')

    def test_sortie_caisse_bloquee_si_solde_insuffisant(self):
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.post(reverse('sortie-caisse-list'), {
            'montant': '20000', 'motif': 'versement_banque',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sortie_caisse_autorisee_si_solde_suffisant(self):
        self.client.force_authenticate(user=self.gerant_a)
        self.client.post(reverse('versement-list'), {
            'facture': self.facture.id, 'montant': '100000',
            'mode_paiement': Versement.ModePaiement.ESPECES,
        })
        response = self.client.post(reverse('sortie-caisse-list'), {
            'montant': '20000', 'motif': 'versement_banque',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_sortie_caisse_bloquee_sans_session(self):
        SessionCaisse.objects.filter(agence=self.agence_a).delete()
        self.client.force_authenticate(user=self.gerant_a)
        response = self.client.post(reverse('sortie-caisse-list'), {
            'montant': '20000', 'motif': 'versement_banque',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sortie_caisse_apparait_dans_journal(self):
        self.client.force_authenticate(user=self.gerant_a)
        SessionCaisse.objects.filter(agence=self.agence_a).update(montant_ouverture='100000')
        self.client.post(reverse('sortie-caisse-list'), {
            'montant': '20000', 'motif': 'versement_banque', 'description': 'Depot BICICI',
        })
        response = self.client.get(reverse('caisse-journal'))
        descriptions = [m['description'] for m in response.data]
        self.assertIn('Depot BICICI', descriptions)
