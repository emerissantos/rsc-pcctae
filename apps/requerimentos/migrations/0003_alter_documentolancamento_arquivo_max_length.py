from django.db import migrations, models

import apps.requerimentos.models


class Migration(migrations.Migration):
    dependencies = [
        ("requerimentos", "0002_alter_documentolancamento_arquivo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="documentolancamento",
            name="arquivo",
            field=models.FileField(
                max_length=500,
                upload_to=apps.requerimentos.models.documento_lancamento_upload_to,
            ),
        ),
    ]
