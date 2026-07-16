# Generated for the OAuth/API integration stage.
import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PessoaInstitucional",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("id_institucional", models.BigIntegerField(unique=True, verbose_name="ID institucional")),
                ("nome", models.CharField(max_length=255)),
                ("nome_identificacao", models.CharField(blank=True, max_length=255)),
                ("email_institucional", models.EmailField(blank=True, max_length=254)),
                ("ativo_na_origem", models.BooleanField(default=True)),
                ("sincronizado_em", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "pessoa institucional",
                "verbose_name_plural": "pessoas institucionais",
                "ordering": ["nome", "id_institucional"],
                "indexes": [models.Index(fields=["nome"], name="idx_pessoa_nome")],
            },
        ),
        migrations.CreateModel(
            name="Servidor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("nome_atual", models.CharField(max_length=255)),
                ("nome_identificacao_atual", models.CharField(blank=True, max_length=255)),
                ("email_atual", models.EmailField(blank=True, max_length=254)),
                ("ativo", models.BooleanField(default=True)),
                ("ultima_sincronizacao_em", models.DateTimeField(blank=True, null=True)),
                ("pessoa", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="servidor", to="pessoas.pessoainstitucional")),
            ],
            options={
                "verbose_name": "servidor",
                "verbose_name_plural": "servidores",
                "ordering": ["nome_atual"],
            },
        ),
        migrations.CreateModel(
            name="ExecucaoSincronizacao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("tipo", models.CharField(choices=[("USUARIO", "Usuário"), ("SERVIDOR", "Servidor e vínculos"), ("COMPLETA", "Sincronização completa")], max_length=20)),
                ("id_institucional_consultado", models.BigIntegerField(blank=True, null=True)),
                ("iniciada_em", models.DateTimeField()),
                ("concluida_em", models.DateTimeField(blank=True, null=True)),
                ("situacao", models.CharField(choices=[("INICIADA", "Iniciada"), ("CONCLUIDA", "Concluída"), ("ALERTAS", "Concluída com alertas"), ("FALHOU", "Falhou")], default="INICIADA", max_length=20)),
                ("quantidade_recebida", models.PositiveIntegerField(default=0)),
                ("quantidade_criada", models.PositiveIntegerField(default=0)),
                ("quantidade_atualizada", models.PositiveIntegerField(default=0)),
                ("mensagem_resumida", models.CharField(blank=True, max_length=500)),
                ("identificador_correlacao", models.CharField(blank=True, db_index=True, max_length=64)),
                ("pessoa", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="sincronizacoes", to="pessoas.pessoainstitucional")),
            ],
            options={
                "verbose_name": "execução de sincronização",
                "verbose_name_plural": "execuções de sincronização",
                "ordering": ["-iniciada_em"],
            },
        ),
        migrations.CreateModel(
            name="VinculoFuncional",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("provedor_origem", models.CharField(default="ufsb_api", max_length=50)),
                ("id_servidor_externo", models.BigIntegerField(verbose_name="ID externo do servidor")),
                ("siape", models.CharField(max_length=20)),
                ("digito_siape", models.CharField(blank=True, max_length=5)),
                ("id_ativo_externo", models.BigIntegerField(blank=True, null=True)),
                ("id_situacao_externa", models.BigIntegerField(blank=True, null=True)),
                ("id_categoria_externa", models.BigIntegerField(blank=True, null=True)),
                ("id_lotacao_externa", models.BigIntegerField(blank=True, null=True)),
                ("lotacao_nome", models.CharField(blank=True, max_length=255)),
                ("id_unidade_exercicio_externa", models.BigIntegerField(blank=True, null=True)),
                ("unidade_exercicio_nome", models.CharField(blank=True, max_length=255)),
                ("id_cargo_externo", models.BigIntegerField(blank=True, null=True)),
                ("cargo_nome", models.CharField(blank=True, max_length=255)),
                ("id_tipo_formacao_externo", models.BigIntegerField(blank=True, null=True)),
                ("regime_trabalho", models.IntegerField(blank=True, null=True)),
                ("data_admissao", models.DateField(blank=True, null=True)),
                ("ativo", models.BooleanField(default=True)),
                ("ultima_sincronizacao_em", models.DateTimeField(blank=True, null=True)),
                ("servidor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="vinculos", to="pessoas.servidor")),
            ],
            options={
                "verbose_name": "vínculo funcional",
                "verbose_name_plural": "vínculos funcionais",
                "ordering": ["-ativo", "siape", "id_servidor_externo"],
                "indexes": [
                    models.Index(fields=["siape"], name="idx_vinculo_siape"),
                    models.Index(fields=["ativo"], name="idx_vinculo_ativo"),
                    models.Index(fields=["id_situacao_externa"], name="idx_vinculo_situacao"),
                    models.Index(fields=["id_categoria_externa"], name="idx_vinculo_categoria"),
                ],
                "constraints": [models.UniqueConstraint(fields=("provedor_origem", "id_servidor_externo"), name="uniq_vinculo_provedor_servidor")],
            },
        ),
    ]
