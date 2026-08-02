import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('depenses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategorieDepense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, unique=True)),
                ('actif', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Categorie de depense',
                'verbose_name_plural': 'Categories de depense',
                'ordering': ['nom'],
            },
        ),
        migrations.AddField(
            model_name='depense',
            name='categorie_fk',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='depenses_temp',
                to='depenses.categoriedepense',
            ),
        ),
    ]
