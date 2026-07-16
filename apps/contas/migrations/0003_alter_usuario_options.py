# Generated for RSC-PCCTAE 0.7.0.

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("contas", "0002_identidade_pessoa"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="usuario",
            options={
                "ordering": ["username"],
                "permissions": [
                    ("importar_usuario_sig", "Pode importar usuário do SIG"),
                    ("simular_usuario", "Pode simular acesso de outro usuário"),
                ],
                "verbose_name": "usuário",
                "verbose_name_plural": "usuários",
            },
        ),
    ]
