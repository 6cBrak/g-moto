import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('depenses', '0003_migrer_categories_depense'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='depense',
            name='categorie',
        ),
        migrations.RenameField(
            model_name='depense',
            old_name='categorie_fk',
            new_name='categorie',
        ),
        migrations.AlterField(
            model_name='depense',
            name='categorie',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='depenses',
                to='depenses.categoriedepense',
            ),
        ),
    ]
