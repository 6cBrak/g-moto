from reportlab.lib.units import mm


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
