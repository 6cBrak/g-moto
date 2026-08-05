import logging

logger = logging.getLogger(__name__)

METHODES_TRACEES = {'POST', 'PUT', 'PATCH', 'DELETE'}
CHEMINS_EXCLUS = ('/api/auth/',)


class JournalActiviteMiddleware:
    """Enregistre chaque action d'ecriture reussie de l'API dans JournalActivite.

    S'execute apres la vue (donc apres l'authentification DRF, qui reporte
    l'utilisateur authentifie sur request.user) pour savoir qui a fait quoi.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            self._journaliser(request, response)
        except Exception:
            logger.exception("Echec de journalisation de l'activite")
        return response

    def _journaliser(self, request, response):
        if request.method not in METHODES_TRACEES:
            return
        if not request.path.startswith('/api/') or request.path.startswith(CHEMINS_EXCLUS):
            return
        if response.status_code >= 400:
            return
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return

        from .models import JournalActivite

        segments = [s for s in request.path.split('/') if s]
        # segments[0] == 'api'
        ressource = segments[1] if len(segments) > 1 else ''
        deuxieme = segments[2] if len(segments) > 2 else ''
        troisieme = segments[3] if len(segments) > 3 else ''
        objet_id = deuxieme if deuxieme.isdigit() else ''
        action = troisieme or (deuxieme if deuxieme and not deuxieme.isdigit() else '')

        if request.method == 'DELETE':
            methode = JournalActivite.Methode.SUPPRESSION
        elif action:
            methode = JournalActivite.Methode.ACTION
        elif request.method == 'POST' and not objet_id:
            methode = JournalActivite.Methode.CREATION
        else:
            methode = JournalActivite.Methode.MODIFICATION

        JournalActivite.objects.create(
            utilisateur=user,
            utilisateur_username=user.username,
            agence=getattr(user, 'agence', None),
            methode=methode,
            ressource=ressource,
            objet_id=objet_id,
            chemin=request.path,
        )
