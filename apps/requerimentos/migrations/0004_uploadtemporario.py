# Generated manually for asynchronous temporary uploads.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import apps.requerimentos.models

class Migration(migrations.Migration):
    dependencies = [
        ("pontuacao", "0001_initial"),
        ("requerimentos", "0003_alter_documentolancamento_arquivo_max_length"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="UploadTemporario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(default=__import__('uuid').uuid4, editable=False, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("arquivo", models.FileField(max_length=500, upload_to=apps.requerimentos.models.upload_temporario_upload_to)),
                ("nome_original", models.CharField(max_length=255)),
                ("tipo_mime", models.CharField(blank=True, max_length=150)),
                ("tamanho_bytes", models.PositiveBigIntegerField(default=0)),
                ("sha256", models.CharField(blank=True, db_index=True, max_length=64)),
                ("status", models.CharField(choices=[("CONCLUIDO", "Concluído"), ("VINCULADO", "Vinculado"), ("ERRO", "Erro")], db_index=True, default="CONCLUIDO", max_length=20)),
                ("expira_em", models.DateTimeField(db_index=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="requerimentos_uploadtemporario_criados", to=settings.AUTH_USER_MODEL, verbose_name="criado por")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="requerimentos_uploadtemporario_atualizados", to=settings.AUTH_USER_MODEL, verbose_name="atualizado por")),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="uploads_temporarios", to="pontuacao.itempontuacao")),
                ("requerimento", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="uploads_temporarios", to="requerimentos.requerimento")),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="uploads_temporarios_rsc", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "upload temporário", "verbose_name_plural": "uploads temporários", "ordering": ["created_at"]},
        ),
        migrations.AddIndex(model_name="uploadtemporario", index=models.Index(fields=["usuario", "status", "expira_em"], name="idx_upload_tmp_usuario_status")),
    ]
