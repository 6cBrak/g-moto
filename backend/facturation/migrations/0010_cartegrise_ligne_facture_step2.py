from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('facturation', '0009_cartegrise_migrer_vers_ligne_facture'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cartegrise',
            name='facture',
        ),
        migrations.AlterField(
            model_name='cartegrise',
            name='ligne_facture',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='carte_grise',
                to='facturation.lignefacture',
            ),
        ),
    ]
