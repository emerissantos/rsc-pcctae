from django.db import migrations, models

import apps.requerimentos.models


class Migration(migrations.Migration):
    dependencies = [
        ("requerimentos", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="documentolancamento",
            name="arquivo",
            field=models.FileField(
                upload_to=apps.requerimentos.models.documento_lancamento_upload_to
            ),
        ),
    ]
