from decimal import ROUND_HALF_UP, Decimal

from reportlab.lib.units import mm

UNITES = [
    'zéro', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf', 'dix',
    'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize',
]
DIZAINES = {2: 'vingt', 3: 'trente', 4: 'quarante', 5: 'cinquante', 6: 'soixante'}


def _moins_de_cent(n, final):
    if n < 17:
        return UNITES[n]
    if n < 20:
        return f"dix-{UNITES[n - 10]}"
    if n < 70:
        dizaine, unite = divmod(n, 10)
        base = DIZAINES[dizaine]
        if unite == 0:
            return base
        return f"{base} et un" if unite == 1 else f"{base}-{UNITES[unite]}"
    if n < 80:
        return 'soixante et onze' if n == 71 else f"soixante-{_moins_de_cent(n - 60, final)}"
    if n == 80:
        return 'quatre-vingts' if final else 'quatre-vingt'
    return f"quatre-vingt-{_moins_de_cent(n - 80, final)}"


def _moins_de_mille(n, final):
    """`final` : le groupe termine le nombre (accord de "cents" et "quatre-vingts")."""
    centaines, reste = divmod(n, 100)
    parts = []
    if centaines:
        mot = 'cent' if centaines == 1 else f"{UNITES[centaines]} cent"
        parts.append(mot + ('s' if centaines > 1 and reste == 0 and final else ''))
    if reste:
        parts.append(_moins_de_cent(reste, final))
    return ' '.join(parts)


def nombre_en_lettres(n):
    if n == 0:
        return UNITES[0]
    milliards, millions = divmod(n, 10 ** 9)
    millions, milliers = divmod(millions, 10 ** 6)
    milliers, reste = divmod(milliers, 1000)

    parts = []
    if milliards:
        parts.append(f"{_moins_de_mille(milliards, True)} milliard{'s' if milliards > 1 else ''}")
    if millions:
        parts.append(f"{_moins_de_mille(millions, True)} million{'s' if millions > 1 else ''}")
    if milliers:
        parts.append('mille' if milliers == 1 else f"{_moins_de_mille(milliers, False)} mille")
    if reste:
        parts.append(_moins_de_mille(reste, True))
    return ' '.join(parts)


def montant_en_lettres(montant):
    """Ex. 1500000 -> 'un million cinq cent mille francs CFA'."""
    n = int(Decimal(montant).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    lettres = nombre_en_lettres(n)
    if n and n % 10 ** 6 == 0:
        lettres += ' de'
    return f"{lettres} {'franc' if n <= 1 else 'francs'} CFA"


def dessiner_entete(doc, agence, y, width):
    """Dessine le logo et les coordonnees de l'agence en haut d'un PDF reportlab.

    Retourne le y sous l'entete (avec une ligne de separation), pret pour le contenu suivant.
    """
    x_texte = 20 * mm
    if agence.logo:
        try:
            doc.drawImage(
                agence.logo.path, 20 * mm, y - 18 * mm, width=18 * mm, height=18 * mm,
                preserveAspectRatio=True, mask='auto',
            )
            x_texte = 42 * mm
        except (OSError, ValueError):
            pass

    haut = y
    doc.setFont('Helvetica-Bold', 14)
    doc.drawString(x_texte, haut, agence.nom_commercial or agence.nom)
    haut -= 5 * mm

    doc.setFont('Helvetica', 9)
    lignes = []
    if agence.adresse:
        lignes.append(agence.adresse)
    contact = ' - '.join(filter(None, [agence.telephone, agence.email]))
    if contact:
        lignes.append(contact)
    identifiants = ' - '.join(filter(None, [
        f"RCCM {agence.rccm}" if agence.rccm else '',
        f"NIF {agence.nif}" if agence.nif else '',
    ]))
    if identifiants:
        lignes.append(identifiants)
    if agence.site_web:
        lignes.append(agence.site_web)

    for ligne in lignes:
        doc.drawString(x_texte, haut, ligne)
        haut -= 4.5 * mm

    bas_entete = min(haut, y - 20 * mm) - 3 * mm
    doc.setLineWidth(0.5)
    doc.line(20 * mm, bas_entete, width - 20 * mm, bas_entete)
    return bas_entete - 8 * mm
