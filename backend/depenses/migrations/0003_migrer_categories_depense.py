from django.db import migrations

DEFAULTS = [
    ('loyer', 'Loyer'),
    ('salaire', 'Salaire'),
    ('carburant', 'Carburant'),
    ('entretien', 'Entretien'),
    ('fourniture', 'Fourniture'),
    ('transport', 'Transport'),
    ('autre', 'Autre'),
]


def migrer_donnees(apps, schema_editor):
    CategorieDepense = apps.get_model('depenses', 'CategorieDepense')
    Depense = apps.get_model('depenses', 'Depense')

    mapping = {}
    for slug, label in DEFAULTS:
        categorie, _ = CategorieDepense.objects.get_or_create(nom=label)
        mapping[slug] = categorie

    for depense in Depense.objects.all():
        slug = depense.categorie
        categorie = mapping.get(slug)
        if categorie is None:
            categorie, _ = CategorieDepense.objects.get_or_create(nom=slug or 'Autre')
            mapping[slug] = categorie
        depense.categorie_fk = categorie
        depense.save(update_fields=['categorie_fk'])


def inverser(apps, schema_editor):
    """Pas de retour en arriere automatique : les categories deviennent des donnees libres."""


class Migration(migrations.Migration):

    dependencies = [
        ('depenses', '0002_categoriedepense_categorie_fk'),
    ]

    operations = [
        migrations.RunPython(migrer_donnees, inverser),
    ]
