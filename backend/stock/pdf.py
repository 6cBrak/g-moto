from collections import Counter
from io import BytesIO

from django.utils import timezone
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from core.pdf_utils import dessiner_entete, tronquer

LARGEUR, HAUTEUR = landscape(A4)
MARGE = 15 * mm
FIN = LARGEUR - MARGE
HAUTEUR_LIGNE = 6.2 * mm
MARGE_BAS = 16 * mm


def _colonnes(afficher_agence):
    """(titre, largeur en mm, fonction d'extraction) ; les largeurs somment a la zone utile."""
    colonnes = [
        ('N°', 11, None),
        ('N° CHÂSSIS', 56, lambda m: m.numero_serie),
        ('MARQUE / TYPE', 56, lambda m: str(m.type_moto)),
        ('COULEUR', 30, lambda m: m.couleur.nom),
        ('N° ARRIVAGE', 36, lambda m: m.arrivage.numero_bon),
        ('DATE ARRIVAGE', 32, lambda m: m.arrivage.date_arrivage.strftime('%d/%m/%Y')),
    ]
    if afficher_agence:
        colonnes.append(('AGENCE', 28, lambda m: m.agence.nom))
    colonnes.append(('STATUT', 0, lambda m: m.get_statut_display()))
    reste = (FIN - MARGE) / mm - sum(largeur for _, largeur, _ in colonnes)
    return [(t, reste if largeur == 0 else largeur, f) for t, largeur, f in colonnes]


class _ListeMotosPdf:
    def __init__(self, motos, agence, criteres, utilisateur):
        self.motos = list(motos)
        self.agence = agence
        self.criteres = criteres
        self.utilisateur = utilisateur
        self.buffer = BytesIO()
        self.doc = canvas.Canvas(self.buffer, pagesize=landscape(A4))
        self.page = 1
        self.y = 0
        agences = {m.agence_id for m in self.motos}
        self.colonnes = _colonnes(afficher_agence=len(agences) > 1)

    def _entete_page(self):
        doc = self.doc
        if self.agence:
            self.y = dessiner_entete(doc, self.agence, HAUTEUR - 14 * mm, LARGEUR, marge=MARGE)
        else:
            self.y = HAUTEUR - 18 * mm
        doc.setFont('Helvetica-Bold', 15)
        doc.drawString(MARGE, self.y, 'LISTE DES MOTOS')
        doc.setFont('Helvetica', 9)
        maintenant = timezone.now()
        doc.drawRightString(
            FIN, self.y, f"Édité le {maintenant:%d/%m/%Y à %H:%M} par {self.utilisateur.username}",
        )
        self.y -= 5.5 * mm
        doc.setFont('Helvetica', 9.5)
        for ligne in self.criteres:
            doc.drawString(MARGE, self.y, tronquer(ligne, 'Helvetica', 9.5, FIN - MARGE))
            self.y -= 4.8 * mm
        doc.setFont('Helvetica-Bold', 10)
        doc.drawString(MARGE, self.y, f"Total : {len(self.motos)} moto{'s' if len(self.motos) > 1 else ''}")
        self.y -= 7 * mm

    def _entete_tableau(self):
        doc = self.doc
        doc.setFillGray(0.88)
        doc.rect(MARGE, self.y - 1.8 * mm, FIN - MARGE, HAUTEUR_LIGNE, stroke=0, fill=1)
        doc.setFillGray(0)
        doc.setFont('Helvetica-Bold', 8.5)
        x = MARGE
        for titre, largeur, _ in self.colonnes:
            doc.drawString(x + 1.5 * mm, self.y, titre)
            x += largeur * mm
        self.y -= HAUTEUR_LIGNE

    def _pied_page(self):
        self.doc.setFont('Helvetica', 8)
        self.doc.setFillGray(0.4)
        self.doc.drawCentredString(LARGEUR / 2, 8 * mm, f"Page {self.page}")
        self.doc.setFillGray(0)

    def _nouvelle_page(self):
        self._pied_page()
        self.doc.showPage()
        self.page += 1
        self.y = HAUTEUR - 15 * mm
        self._entete_tableau()

    def _ligne(self, index, moto):
        doc = self.doc
        doc.setFont('Helvetica', 9)
        x = MARGE
        for titre, largeur, extraire in self.colonnes:
            valeur = str(index) if extraire is None else extraire(moto)
            doc.drawString(x + 1.5 * mm, self.y, tronquer(valeur, 'Helvetica', 9, largeur * mm - 3 * mm))
            x += largeur * mm
        doc.setLineWidth(0.3)
        doc.setStrokeGray(0.8)
        doc.line(MARGE, self.y - 1.8 * mm, FIN, self.y - 1.8 * mm)
        doc.setStrokeGray(0)
        self.y -= HAUTEUR_LIGNE

    def _recapitulatif(self):
        doc = self.doc
        par_type = Counter(str(m.type_moto) for m in self.motos)
        besoin = (len(par_type) + 3) * HAUTEUR_LIGNE
        if self.y - besoin < MARGE_BAS:
            self._nouvelle_page()
        self.y -= 4 * mm
        doc.setFont('Helvetica-Bold', 10)
        doc.drawString(MARGE, self.y, 'RÉCAPITULATIF PAR TYPE')
        self.y -= HAUTEUR_LIGNE
        largeur = max(stringWidth(t, 'Helvetica', 9) for t in par_type) + 30 * mm
        doc.setFont('Helvetica', 9)
        for type_moto in sorted(par_type):
            doc.drawString(MARGE, self.y, type_moto)
            doc.drawRightString(MARGE + largeur, self.y, str(par_type[type_moto]))
            doc.setLineWidth(0.3)
            doc.setStrokeGray(0.8)
            doc.line(MARGE, self.y - 1.8 * mm, MARGE + largeur, self.y - 1.8 * mm)
            doc.setStrokeGray(0)
            self.y -= HAUTEUR_LIGNE
        doc.setFont('Helvetica-Bold', 9.5)
        doc.drawString(MARGE, self.y, 'TOTAL')
        doc.drawRightString(MARGE + largeur, self.y, str(len(self.motos)))

    def generer(self):
        self._entete_page()
        self._entete_tableau()
        if not self.motos:
            self.doc.setFont('Helvetica-Oblique', 10)
            self.doc.drawString(MARGE + 1.5 * mm, self.y, 'Aucune moto ne correspond à ces critères.')
        for index, moto in enumerate(self.motos, start=1):
            if self.y < MARGE_BAS:
                self._nouvelle_page()
            self._ligne(index, moto)
        if self.motos:
            self._recapitulatif()
        self._pied_page()
        self.doc.showPage()
        self.doc.save()
        self.buffer.seek(0)
        return self.buffer


def generer_pdf_liste_motos(motos, agence, criteres, utilisateur):
    return _ListeMotosPdf(motos, agence, criteres, utilisateur).generer()
