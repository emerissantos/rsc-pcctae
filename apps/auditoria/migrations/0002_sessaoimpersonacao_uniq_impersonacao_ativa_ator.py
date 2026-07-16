from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auditoria', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='sessaoimpersonacao',
            constraint=models.UniqueConstraint(condition=models.Q(('encerrada_em__isnull', True)), fields=('ator',), name='uniq_impersonacao_ativa_ator'),
        ),
    ]
