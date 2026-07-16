import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contas", "0001_initial"),
        ("pessoas", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="identidadeexterna",
            name="pessoa",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="identidades_externas",
                to="pessoas.pessoainstitucional",
            ),
        ),
    ]
