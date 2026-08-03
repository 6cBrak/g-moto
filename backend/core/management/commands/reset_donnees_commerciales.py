from django.core.management.base import BaseCommand

from core.utils import compter_donnees_commerciales, purger_donnees_commerciales


class Command(BaseCommand):
    help = (
        "Supprime les donnees commerciales de test avant le lancement en production : "
        "factures et documents lies, caisse, clients et depots-vente. "
        "Le module stock (motos, arrivages, historique) n'est pas touche, "
        "hormis la remise en stock des motos vendues/en depot."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Affiche ce qui serait supprime sans rien modifier.",
        )
        parser.add_argument(
            '--yes', action='store_true',
            help="Ne pas demander de confirmation interactive.",
        )

    def handle(self, *args, **options):
        counts = compter_donnees_commerciales()

        self.stdout.write("Donnees qui seront supprimees :")
        for label, count in counts.items():
            self.stdout.write(f"  - {label}: {count}")

        if options['dry_run']:
            self.stdout.write(self.style.WARNING("Dry-run: aucune suppression effectuee."))
            return

        if not options['yes']:
            reponse = input(
                "Cette action est irreversible. Taper 'SUPPRIMER' pour confirmer : ",
            )
            if reponse != 'SUPPRIMER':
                self.stdout.write(self.style.ERROR("Annule."))
                return

        purger_donnees_commerciales()
        self.stdout.write(self.style.SUCCESS("Donnees commerciales de test supprimees."))
