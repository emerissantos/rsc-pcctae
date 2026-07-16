# Generated for RSC-PCCTAE 0.7.0.

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="EventoAuditoria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("tipo", models.CharField(choices=[("IMPORTACAO_USUARIO_SIG", "Importação de usuário do SIG"), ("ACAO_BLOQUEADA_IMPERSONACAO", "Ação bloqueada durante simulação")], db_index=True, max_length=50)),
                ("descricao", models.CharField(max_length=500)),
                ("dados", models.JSONField(blank=True, default=dict)),
                ("request_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("endereco_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.CharField(blank=True, max_length=500)),
                ("ator", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="eventos_auditoria_realizados", to=settings.AUTH_USER_MODEL)),
                ("usuario_afetado", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="eventos_auditoria_recebidos", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "evento de auditoria",
                "verbose_name_plural": "eventos de auditoria",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="SessaoImpersonacao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("justificativa", models.CharField(max_length=500)),
                ("iniciada_em", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("encerrada_em", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("motivo_encerramento", models.CharField(blank=True, max_length=250)),
                ("request_id_inicio", models.CharField(blank=True, db_index=True, max_length=64)),
                ("endereco_ip_inicio", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent_inicio", models.CharField(blank=True, max_length=500)),
                ("ator", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sessoes_impersonacao_iniciadas", to=settings.AUTH_USER_MODEL)),
                ("encerrada_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="sessoes_impersonacao_encerradas", to=settings.AUTH_USER_MODEL)),
                ("usuario_simulado", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sessoes_em_que_foi_simulado", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "sessão de simulação de usuário",
                "verbose_name_plural": "sessões de simulação de usuário",
                "ordering": ["-iniciada_em"],
            },
        ),
        migrations.AddIndex(
            model_name="eventoauditoria",
            index=models.Index(fields=["tipo", "created_at"], name="idx_audit_tipo_data"),
        ),
        migrations.AddIndex(
            model_name="sessaoimpersonacao",
            index=models.Index(fields=["ator", "encerrada_em"], name="idx_imp_ator_ativa"),
        ),
        migrations.AddIndex(
            model_name="sessaoimpersonacao",
            index=models.Index(fields=["usuario_simulado", "iniciada_em"], name="idx_imp_alvo_data"),
        ),
    ]
