from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0004_sortiecaisse_fournisseur_alter_sortiecaisse_motif'),
    ]

    operations = [
        migrations.AddField(
            model_name='versement',
            name='numero_recu',
            field=models.CharField(blank=True, max_length=30, null=True, unique=True),
        ),
    ]
