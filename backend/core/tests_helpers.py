import re
import zlib
from base64 import a85decode


def extraire_texte_pdf(reponse):
    """Texte brut d'un PDF genere par reportlab (flux ASCII85 + Flate), pour les assertions de tests."""
    contenu = b''.join(reponse.streaming_content)
    texte = ''
    for flux in re.findall(rb'stream\r?\n(.*?)endstream', contenu, re.S):
        try:
            texte += zlib.decompress(a85decode(flux.strip(), adobe=True)).decode('latin-1')
        except Exception:
            continue
    return texte
