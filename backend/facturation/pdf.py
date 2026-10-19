from decimal import Decimal
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from caisse.models import Versement
from core.pdf_utils import (
    dessiner_champ, dessiner_entete, formater_montant, montant_en_lettres,
)

MARGE = 20 * mm
LARGEUR_UTILE = A4[0] - 2 * MARGE
PAS_LIGNE = 8 * mm
COL_GAUCHE = MARGE + 4 * mm
COL_DROITE = MARGE + 90 * mm
FIN_CADRE = A4[0] - MARGE - 4 * mm
X_NUMERO = MARGE + 8 * mm
X_FILET_NUMERO = MARGE + 13 * mm
COL_LIGNE = MARGE + 16 * mm

POLICE_LABEL = ('Helvetica-Bold', 9.5)
POLICE_VALEUR = ('Helvetica', 10.5)


class _FacturePdf:
    def __init__(self, facture):
        self.facture = facture
        self.buffer = BytesIO()
        self.doc = canvas.Canvas(self.buffer, pagesize=A4)
        self.largeur, self.hauteur = A4
        self.y = 0
        self.cadre_haut = None

    # --- primitives ---

    def _champ(self, label, valeur, x, y, x_fin):
        dessiner_champ(self.doc, label, valeur, x, y, x_fin, POLICE_LABEL, POLICE_VALEUR)

    def _ouvrir_cadre(self):
        self.cadre_haut = self.y
        self.y -= 8 * mm

    def _fermer_cadre(self):
        bas = self.y + PAS_LIGNE - 3 * mm
        self.doc.setLineWidth(0.8)
        self.doc.roundRect(MARGE, bas, LARGEUR_UTILE, self.cadre_haut - bas, 3 * mm)
        self.y = bas
        self.cadre_haut = None

    def _nouvelle_page(self):
        self.doc.showPage()
        self.y = self.hauteur - MARGE

    def _assurer_place(self, hauteur, dans_cadre=False, marge_bas=MARGE):
        """Passe a une nouvelle page s'il manque de la place. Retourne True si c'est le cas."""
        if self.y - hauteur >= marge_bas:
            return False
        if dans_cadre:
            self._fermer_cadre()
        self._nouvelle_page()
        if dans_cadre:
            self._ouvrir_cadre()
        return True

    # --- sections ---

    def _titre(self):
        doc, facture = self.doc, self.facture
        self.y = dessiner_entete(doc, facture.agence, self.hauteur - 25 * mm, self.largeur)

        doc.setFont('Helvetica-Bold', 16)
        doc.drawString(MARGE, self.y, f"FACTURE N° {facture.numero_facture}")

        # cases Jour / Mois / Annee
        date = facture.date_facture
        largeurs = [20 * mm, 20 * mm, 28 * mm]
        x = self.largeur - MARGE - sum(largeurs)
        haut = self.y + 6 * mm
        doc.setLineWidth(0.8)
        doc.rect(x, haut - 12 * mm, sum(largeurs), 12 * mm)
        doc.line(x, haut - 5 * mm, x + sum(largeurs), haut - 5 * mm)
        for label, valeur, largeur in zip(
            ['Jour', 'Mois', 'Année'], [f"{date:%d}", f"{date:%m}", f"{date:%Y}"], largeurs,
        ):
            doc.setFont('Helvetica-Bold', 8)
            doc.drawCentredString(x + largeur / 2, haut - 3.7 * mm, label)
            doc.setFont('Helvetica', 10)
            doc.drawCentredString(x + largeur / 2, haut - 10 * mm, valeur)
            if x + largeur < self.largeur - MARGE:
                doc.line(x + largeur, haut, x + largeur, haut - 12 * mm)
            x += largeur
        self.y -= 14 * mm

    def _client(self):
        facture = self.facture
        numeros = []
        for ligne in facture.lignes.all():
            if ligne.moto and ligne.moto.arrivage.numero_bon not in numeros:
                numeros.append(ligne.moto.arrivage.numero_bon)
        fin = self.largeur - MARGE
        self._champ('Nom et prénom(s) :', facture.client.nom, MARGE, self.y, fin)
        self.y -= PAS_LIGNE
        self._champ('Adresse :', facture.client.adresse, MARGE, self.y, fin)
        self.y -= PAS_LIGNE
        self._champ("N° d'arrivage :", ', '.join(numeros), MARGE, self.y, fin)
        self.y -= PAS_LIGNE + 2 * mm

    def _separateur(self):
        self.y -= 3 * mm
        self.doc.setLineWidth(0.5)
        self.doc.setStrokeGray(0.45)
        self.doc.line(COL_GAUCHE, self.y + 5.5 * mm, FIN_CADRE, self.y + 5.5 * mm)
        self.doc.setStrokeGray(0)

    def _separateur_totaux(self):
        self.y -= 5 * mm
        self.doc.setLineWidth(1)
        self.doc.line(MARGE, self.y + 8 * mm, A4[0] - MARGE, self.y + 8 * mm)

    def _numeroter(self, numero, haut, bas):
        """Numero d'ordre dans la marge gauche du bloc, separe des champs par un filet."""
        doc = self.doc
        doc.setLineWidth(0.5)
        doc.setStrokeGray(0.45)
        doc.line(X_FILET_NUMERO, haut, X_FILET_NUMERO, bas)
        doc.setStrokeGray(0)
        doc.setFont('Helvetica-Bold', 15)
        doc.drawCentredString(X_NUMERO, (haut + bas) / 2 - 2 * mm, str(numero))

    def _ligne_moto(self, ligne):
        moto = ligne.moto
        self._champ('MOTO :', str(moto.type_moto), COL_LIGNE, self.y, COL_DROITE - 4 * mm)
        self._champ('COULEUR :', moto.couleur.nom, COL_DROITE, self.y, FIN_CADRE)
        self.y -= PAS_LIGNE
        self._champ('MARQUE :', moto.type_moto.marque.nom, COL_LIGNE, self.y, COL_DROITE - 4 * mm)
        self._champ('TYPE :', moto.type_moto.nom, COL_DROITE, self.y, FIN_CADRE)
        self.y -= PAS_LIGNE
        self._champ('CHÂSSIS N° :', moto.numero_serie, COL_LIGNE, self.y, FIN_CADRE)
        self.y -= PAS_LIGNE
        self._champ('MONTANT :', formater_montant(ligne.montant), COL_LIGNE, self.y, FIN_CADRE)
        self.y -= PAS_LIGNE

    def _ligne_article(self, ligne):
        designation = ligne.designation
        if ligne.modele_casque:
            designation = f"Casque {ligne.modele_casque.nom}"
        self._champ('ARTICLE :', designation, COL_LIGNE, self.y, FIN_CADRE)
        self.y -= PAS_LIGNE
        self._champ('QUANTITÉ :', ligne.quantite, COL_LIGNE, self.y, COL_DROITE - 4 * mm)
        self._champ('PRIX UNITAIRE :', formater_montant(ligne.prix_unitaire), COL_DROITE, self.y, FIN_CADRE)
        self.y -= PAS_LIGNE
        self._champ('MONTANT :', formater_montant(ligne.montant), COL_LIGNE, self.y, FIN_CADRE)
        self.y -= PAS_LIGNE

    def _cadre_lignes(self):
        facture = self.facture
        lignes = list(facture.lignes.all())
        total = facture.total
        avance = sum(
            (v.montant for v in facture.versements.all() if v.statut == Versement.Statut.VALIDE),
            Decimal('0'),
        )

        self._ouvrir_cadre()
        for index, ligne in enumerate(lignes):
            nouvelle_page = self._assurer_place(4 * PAS_LIGNE + 3 * mm, dans_cadre=True)
            if index and not nouvelle_page:
                self._separateur()
            haut = self.y + 5 * mm
            if ligne.moto:
                self._ligne_moto(ligne)
            else:
                self._ligne_article(ligne)
            self._numeroter(index + 1, haut, self.y + PAS_LIGNE - 3 * mm)

        self._assurer_place(3 * PAS_LIGNE + 5 * mm, dans_cadre=True)
        self._separateur_totaux()
        if len(lignes) > 1:
            self._champ('MONTANT TOTAL :', formater_montant(total), COL_GAUCHE, self.y, FIN_CADRE)
            self.y -= PAS_LIGNE
        self._champ('AVANCE VERSÉE :', formater_montant(avance), COL_GAUCHE, self.y, FIN_CADRE)
        self.y -= PAS_LIGNE
        self._champ('RESTE À PAYER :', formater_montant(total - avance), COL_GAUCHE, self.y, FIN_CADRE)
        self.y -= PAS_LIGNE
        self._fermer_cadre()

    def _pied(self):
        doc, facture = self.doc, self.facture
        self._assurer_place(58 * mm, marge_bas=12 * mm)
        nom_agence = facture.agence.nom_commercial or facture.agence.nom

        self.y -= 6 * mm
        doc.setFont('Helvetica-Bold', 9.5)
        doc.drawString(MARGE, self.y, f"Pour tout achat de moto chez {nom_agence.upper()}, recevez :")
        self.y -= 5.5 * mm
        doc.setFont('Helvetica-Bold', 9)
        for texte in [
            '1) Une garantie bloc moteur de 6 mois',
            '2) Un casque de sécurité + 01 trousseau de clés',
            '3) Visite de moto 06 mois uniquement pour les tricycles',
        ]:
            doc.drawString(MARGE + 8 * mm, self.y, texte)
            self.y -= 5 * mm

        self.y -= 8 * mm
        label = 'Arrêtée la présente facture à la somme de :'
        doc.setFont('Helvetica-Oblique', 10)
        doc.drawString(MARGE, self.y, label)
        x_texte = MARGE + stringWidth(label, 'Helvetica-Oblique', 10) + 2 * mm
        lettres = montant_en_lettres(facture.total)
        premiere = simpleSplit(lettres, 'Helvetica', 10.5, self.largeur - MARGE - x_texte)
        # le texte qui deborde de la premiere ligne passe sur les lignes suivantes, pleine largeur
        reste = lettres[len(premiere[0]):].strip() if premiere else ''
        suite = simpleSplit(reste, 'Helvetica', 10.5, LARGEUR_UTILE) if reste else []
        doc.setFont('Helvetica', 10.5)
        doc.drawString(x_texte, self.y, premiere[0] if premiere else '')
        doc.setLineWidth(0.4)
        doc.setDash(1, 2)
        doc.line(x_texte, self.y - 1 * mm, self.largeur - MARGE, self.y - 1 * mm)
        for texte in suite or ['']:
            self.y -= PAS_LIGNE
            doc.drawString(MARGE, self.y, texte)
            doc.line(MARGE, self.y - 1 * mm, self.largeur - MARGE, self.y - 1 * mm)
        doc.setDash()

        self.y -= 14 * mm
        doc.setFont('Helvetica-Oblique', 10)
        doc.drawString(MARGE, self.y, 'Le Responsable')
        doc.drawRightString(self.largeur - MARGE, self.y, 'Le Client')

    def generer(self):
        self._titre()
        self._client()
        self._cadre_lignes()
        self._pied()
        self.doc.showPage()
        self.doc.save()
        self.buffer.seek(0)
        return self.buffer


def generer_pdf_facture(facture):
    return _FacturePdf(facture).generer()
