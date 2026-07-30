# Prompt projet — Application de gestion de vente de motos multi-agences

## Contexte

Je veux construire une application web complète de gestion de vente de motos, en remplacement d'une ancienne application Microsoft Access. L'application doit gérer plusieurs agences/points de vente.

Construis le projet de A à Z : structure des dossiers, backend, frontend, modèles de données, API, authentification, et une première version fonctionnelle de chaque module. Procède module par module en me montrant ton avancement, ne fais pas tout d'un coup sans validation intermédiaire.

## Stack technique imposée

**Backend**
- Django + Django REST Framework (DRF)
- Authentification par JWT via `djangorestframework-simplejwt`
- Base de données MySQL

**Frontend**
- React + Vite
- Tailwind CSS
- React Router pour la navigation
- TanStack Query pour la gestion des appels API et du cache
- Zustand pour l'état global (utilisateur connecté, agence active)

## Architecture générale

- Une seule base de données MySQL partagée entre toutes les agences.
- Chaque enregistrement métier (moto, facture, versement, dépense, client...) est rattaché à une agence via une clé étrangère `agence`.
- Un système de rôles détermine ce que chaque utilisateur peut voir/faire :
  - **Vendeur / Caissier** : accès limité à son agence
  - **Gérant** : accès à son agence + rapports consolidés
  - **Admin** : accès total, comparaison inter-agences
- Le filtrage par agence doit être géré au niveau des permissions DRF (querysets filtrés automatiquement selon l'utilisateur connecté), pas côté frontend uniquement.

## Modules fonctionnels à implémenter

### 1. Core (utilisateurs, agences, rôles)
- CRUD Agences
- CRUD Utilisateurs avec rattachement à une agence et un rôle
- Authentification JWT (login, refresh token, logout)
- Gestion des permissions par rôle

### 2. Catalogue
- CRUD Marques de motos
- CRUD Couleurs
- CRUD Types/modèles de motos
- CRUD Modèles de casques
- CRUD Fournisseurs

### 3. Stock / Arrivages
- Saisie des arrivages (bon d'arrivage lié à un fournisseur, une agence, une date)
- Chaque moto physique a un numéro de série unique, une marque, un type, une couleur, un statut (en stock / vendue / transférée)
- Historique complet par numéro de série (arrivage → vente → SAV)
- Liste des séries par arrivage
- Modification de facture d'arrivage

### 4. Facturation clients
- Fiche client (nom, contact, adresse, historique d'achats)
- Saisie des déclarations
- Saisie et suivi des cartes grises
- Suivi de retrait des cartes grises
- Suivi de retrait de quittance / CMC
- Génération de facture en PDF
- Réédition de facture

### 5. Caisse / Versements clients
- Journal de caisse (tous les mouvements, filtrable par agence et par période)
- Rapport général des ventes
- Rapport des dépenses
- Liste des clients débiteurs (créances en cours)
- Historique par numéro de série
- Bordereau de livraison (PDF)
- Rapport des ventes par client
- **Mode de paiement** : champ simple à choix (Espèces, Orange Money, Moov Money, Wave, Virement bancaire, Chèque) + champ texte libre optionnel pour la référence de transaction. Aucune intégration d'API de paiement n'est nécessaire pour cette version.

### 6. Dépenses
- CRUD Dépenses par agence, avec catégorie et justificatif

### 7. Stock boutique / Stock général
- Vue d'ensemble du stock disponible par agence et consolidé
- Alertes de stock bas

### 8. Clients (module à ajouter, absent de l'ancienne app)
- Fiche client enrichie avec historique complet
- Relances automatiques (carte grise en retard, quittance en attente)
- Segmentation (clients VIP, débiteurs, revendeurs)

### 9. Rapports & Dashboard
- Dashboard avec KPIs temps réel (ventes du jour, stock critique, trésorerie par agence)
- Rapports comparatifs par période
- Rapports comparatifs par agence

### 10. Après-vente (module à ajouter)
- Suivi de garantie par moto
- Planification d'entretien/révisions

## Modèle de données — entités principales à créer

Agence, Utilisateur (extension du modèle User Django avec rôle + agence), Marque, Couleur, TypeMoto, ModeleCasque, Fournisseur, Arrivage, Moto (avec numéro de série unique, statut, agence), Client, Facture, LigneFacture, CarteGrise, Quittance, Versement (avec mode de paiement), Depense, JournalCaisse, Garantie.

Propose un schéma détaillé avec les relations (clés étrangères, contraintes d'unicité sur les numéros de série) avant de générer les migrations.

## Instructions de travail

1. Commence par la structure du projet (backend + frontend séparés, ou monorepo — propose la meilleure option) et la configuration de base (settings Django, connexion MySQL, configuration JWT, configuration Vite/Tailwind).
2. Mets en place le module Core (utilisateurs, agences, rôles, authentification) en premier — c'est la fondation de tout le reste.
3. Implémente ensuite les modules dans cet ordre : Catalogue → Stock/Arrivages → Facturation clients → Caisse/Versements → Dépenses → Clients → Rapports/Dashboard → Après-vente.
4. Pour chaque module : modèles Django, migrations, serializers DRF, viewsets avec permissions filtrées par agence, endpoints, puis pages React correspondantes (liste, création, édition).
5. Écris des tests basiques pour l'authentification et le filtrage par agence (sécurité critique du projet).
6. Documente les endpoints au fur et à mesure (README ou commentaires DRF).

Pose-moi des questions si un point métier n'est pas clair avant de faire des choix d'architecture irréversibles.
