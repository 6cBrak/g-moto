from io import BytesIO

from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from core.pdf_utils import dessiner_champ, dessiner_entete, formater_montant, montant_en_lettres

from .models import Versement

LARGEUR, HAUTEUR = A5
MARGE = 12 * mm
FIN = LARGEUR - MARGE
PAS = 7 * mm
MAX_MOTOS_AFFICHEES = 2

POLICE_LABEL = ('Helvetica-Bold', 9)
POLICE_VALEUR = ('Helvetica', 10)


class _RecuPdf:
    def __init__(self, versement):
        self.versement = versement
        self.facture = versement.facture
        self.buffer = BytesIO()
        self.doc = canvas.Canvas(self.buffer, pagesize=A5)
        self.y = 0

    def _champ(self, label, valeur, x=MARGE, x_fin=FIN):
        dessiner_champ(self.doc, label, valeur, x, self.y, x_fin, POLICE_LABEL, POLICE_VALEUR)
        self.y -= PAS

    def _situation_compte(self):
        """Total facture, versements precedents et reste a payer apres ce versement."""
        versement, facture = self.versement, self.facture
        cle = (versement.date_versement, versement.id)
        precedents = sum(
            (
                v.montant for v in facture.versements.all()
                if v.statut == Versement.Statut.VALIDE and v.id != versement.id
                and (v.date_versement, v.id) < cle
            ),
            versement.montant * 0,
        )
        total = facture.total
        return total, precedents, total - precedents - versement.montant

    def _titre(self):
        doc, versement = self.doc, self.versement
        self.y = dessiner_entete(doc, versement.agence, HAUTEUR - 14 * mm, LARGEUR, marge=MARGE)
        self.y += 2 * mm

        doc.setFont('Helvetica-Bold', 13)
        doc.drawString(MARGE, self.y, 'REÇU DE VERSEMENT')

        date = versement.date_versement
        largeurs = [14 * mm, 14 * mm, 20 * mm]
        x = FIN - sum(largeurs)
        haut = self.y + 4 * mm
        doc.setLineWidth(0.8)
        doc.rect(x, haut - 10 * mm, sum(largeurs), 10 * mm)
        doc.line(x, haut - 4 * mm, FIN, haut - 4 * mm)
        for label, valeur, largeur in zip(
            ['Jour', 'Mois', 'Année'], [f"{date:%d}", f"{date:%m}", f"{date:%Y}"], largeurs,
        ):
            doc.setFont('Helvetica-Bold', 7)
            doc.drawCentredString(x + largeur / 2, haut - 3 * mm, label)
            doc.setFont('Helvetica', 9)
            doc.drawCentredString(x + largeur / 2, haut - 8.2 * mm, valeur)
            if x + largeur < FIN:
                doc.line(x + largeur, haut, x + largeur, haut - 10 * mm)
            x += largeur

        self.y -= 7 * mm
        doc.setFont('Helvetica-Bold', 11)
        doc.drawString(MARGE, self.y, f"N° {versement.numero_recu or versement.id}")
        self.y -= 9 * mm

    def _client_et_motos(self):
        facture = self.facture
        self._champ('Reçu de :', facture.client.nom)
        self._champ('Adresse :', facture.client.adresse)
        self._champ('Facture N° :', facture.numero_facture)

        motos = [ligne.moto for ligne in facture.lignes.all() if ligne.moto]
        if not motos:
            return
        for moto in motos[:MAX_MOTOS_AFFICHEES]:
            self._champ('MOTO :', f"{moto.type_moto} - {moto.couleur.nom} - {moto.numero_serie}")
        if len(motos) > MAX_MOTOS_AFFICHEES:
            reste = len(motos) - MAX_MOTOS_AFFICHEES
            self.doc.setFont('Helvetica-Oblique', 9)
            self.doc.drawString(MARGE, self.y, f"et {reste} autre{'s' if reste > 1 else ''} moto{'s' if reste > 1 else ''}")
            self.y -= PAS
        numeros = []
        for moto in motos:
            if moto.arrivage.numero_bon not in numeros:
                numeros.append(moto.arrivage.numero_bon)
        self._champ("N° d'arrivage :", ', '.join(numeros))

    def _cadre_montants(self):
        doc, versement = self.doc, self.versement
        total, precedents, reste = self._situation_compte()
        self.y -= 2 * mm
        haut = self.y
        self.y -= 6 * mm

        x, x_fin = MARGE + 4 * mm, FIN - 4 * mm
        self._champ('MODE DE PAIEMENT :', versement.get_mode_paiement_display(), x, x_fin)
        if versement.reference_transaction:
            self._champ('RÉFÉRENCE :', versement.reference_transaction, x, x_fin)
        self._champ('MONTANT DE LA FACTURE :', formater_montant(total), x, x_fin)
        self._champ('VERSEMENTS PRÉCÉDENTS :', formater_montant(precedents), x, x_fin)

        doc.setFont('Helvetica-Bold', 11)
        doc.drawString(x, self.y, 'MONTANT VERSÉ :')
        doc.setFont('Helvetica-Bold', 13)
        doc.drawRightString(x_fin, self.y, formater_montant(versement.montant))
        self.y -= PAS + 1 * mm
        y_reste = self.y
        self._champ('RESTE À PAYER :', formater_montant(max(reste, 0)), x, x_fin)

        bas = self.y + PAS - 3 * mm
        doc.setLineWidth(0.8)
        doc.roundRect(MARGE, bas, FIN - MARGE, haut - bas, 3 * mm)
        self.y = bas

        if reste <= 0 and versement.statut == Versement.Statut.VALIDE:
            self._tampon_solde(y_reste)

    def _tampon_solde(self, y):
        doc = self.doc
        doc.saveState()
        doc.translate(FIN - 24 * mm, y + 1 * mm)
        doc.rotate(12)
        doc.setStrokeColorRGB(0.1, 0.5, 0.2)
        doc.setFillColorRGB(0.1, 0.5, 0.2)
        doc.setLineWidth(1.5)
        doc.roundRect(-14 * mm, -4.5 * mm, 28 * mm, 9 * mm, 1.5 * mm)
        doc.setFont('Helvetica-Bold', 13)
        doc.drawCentredString(0, -1.5 * mm, 'SOLDÉ')
        doc.restoreState()

    def _pied(self):
        doc, versement = self.doc, self.versement
        self.y -= 8 * mm
        label = 'Reçu la somme de :'
        doc.setFont('Helvetica-Oblique', 9.5)
        doc.drawString(MARGE, self.y, label)
        x_texte = MARGE + stringWidth(label, 'Helvetica-Oblique', 9.5) + 2 * mm
        lettres = montant_en_lettres(versement.montant)
        premiere = simpleSplit(lettres, 'Helvetica', 10, FIN - x_texte)[0]
        reste = lettres[len(premiere):].strip()
        suite = simpleSplit(reste, 'Helvetica', 10, FIN - MARGE) if reste else []

        doc.setFont('Helvetica', 10)
        doc.drawString(x_texte, self.y, premiere)
        doc.setLineWidth(0.4)
        doc.setDash(1, 2)
        doc.line(x_texte, self.y - 1 * mm, FIN, self.y - 1 * mm)
        for texte in suite:
            self.y -= PAS
            doc.drawString(MARGE, self.y, texte)
            doc.line(MARGE, self.y - 1 * mm, FIN, self.y - 1 * mm)
        doc.setDash()

        self.y -= 9 * mm
        doc.setFont('Helvetica', 9)
        doc.drawString(MARGE, self.y, f"Encaissé par : {versement.cree_par.username}")
        self.y -= 7 * mm
        doc.setFont('Helvetica-Oblique', 9.5)
        doc.drawString(MARGE, self.y, 'Le Responsable')
        doc.drawRightString(FIN, self.y, 'Le Client')

    def _filigrane_annule(self):
        doc = self.doc
        doc.saveState()
        doc.setFillColorRGB(0.85, 0.1, 0.1)
        doc.setFillAlpha(0.22)
        doc.translate(LARGEUR / 2, HAUTEUR / 2)
        doc.rotate(35)
        doc.setFont('Helvetica-Bold', 60)
        doc.drawCentredString(0, 0, 'ANNULÉ')
        doc.restoreState()

    def generer(self):
        self._titre()
        self._client_et_motos()
        self._cadre_montants()
        self._pied()
        if self.versement.statut == Versement.Statut.ANNULE:
            self._filigrane_annule()
        self.doc.showPage()
        self.doc.save()
        self.buffer.seek(0)
        return self.buffer


def generer_pdf_recu(versement):
    return _RecuPdf(versement).generer()
