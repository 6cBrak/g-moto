from django.db import migrations


def numeroter_versements_existants(apps, schema_editor):
    """Donne un numero de recu aux versements deja enregistres, dans l'ordre de creation."""
    Versement = apps.get_model('caisse', 'Versement')
    sequences = {}
    for versement in Versement.objects.filter(numero_recu__isnull=True).order_by('date_versement', 'id'):
        prefixe = f"R{versement.agence_id:02d}-{versement.date_versement.year}-"
        if prefixe not in sequences:
            dernier = (
                Versement.objects.filter(numero_recu__startswith=prefixe)
                .order_by('-numero_recu').values_list('numero_recu', flat=True).first()
            )
            sequences[prefixe] = int(dernier.rsplit('-', 1)[-1]) if dernier else 0
        sequences[prefixe] += 1
        versement.numero_recu = f"{prefixe}{sequences[prefixe]:05d}"
        versement.save(update_fields=['numero_recu'])


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0005_versement_numero_recu'),
    ]

    operations = [
        migrations.RunPython(numeroter_versements_existants, migrations.RunPython.noop),
    ]
