from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("auditoria", "0002_sessaoimpersonacao_uniq_impersonacao_ativa_ator")]

    operations = [
        migrations.AddField(
            model_name="eventoauditoria",
            name="categoria",
            field=models.CharField(
                choices=[
                    ("AUTENTICACAO", "Autenticação"),
                    ("ACESSO", "Acesso e autorização"),
                    ("CADASTRO", "Cadastro estrutural"),
                    ("REQUERIMENTO", "Requerimento"),
                    ("DOCUMENTO", "Documento"),
                    ("TRIAGEM", "Triagem"),
                    ("IMPERSONACAO", "Simulação de usuário"),
                    ("INTEGRACAO", "Integração institucional"),
                ],
                db_index=True,
                default="ACESSO",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="eventoauditoria",
            name="nivel",
            field=models.CharField(
                choices=[
                    ("INFORMATIVO", "Informativo"),
                    ("ATENCAO", "Atenção"),
                    ("CRITICO", "Crítico"),
                ],
                db_index=True,
                default="INFORMATIVO",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="eventoauditoria",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("LOGIN_SUCESSO", "Login realizado"),
                    ("LOGIN_FALHA", "Falha de login"),
                    ("LOGOUT", "Logout realizado"),
                    ("ACESSO_NEGADO", "Acesso negado"),
                    ("REQUERIMENTO_VISUALIZADO", "Requerimento visualizado"),
                    ("IMPORTACAO_USUARIO_SIG", "Importação de usuário do SIG"),
                    ("CADASTRO_CRIADO", "Cadastro criado"),
                    ("CADASTRO_ALTERADO", "Cadastro alterado"),
                    ("CADASTRO_EXCLUIDO", "Cadastro excluído"),
                    ("REQUERIMENTO_CRIADO", "Requerimento criado"),
                    ("ITEM_REQUERIMENTO_SALVO", "Item do requerimento salvo"),
                    ("ITEM_REQUERIMENTO_REMOVIDO", "Item do requerimento removido"),
                    ("REQUERIMENTO_SUBMETIDO", "Requerimento submetido"),
                    ("UPLOAD_TEMPORARIO_CRIADO", "Upload temporário criado"),
                    ("UPLOAD_TEMPORARIO_REMOVIDO", "Upload temporário removido"),
                    ("DOCUMENTO_ADICIONADO", "Documento adicionado"),
                    ("DOCUMENTO_REMOVIDO", "Documento removido"),
                    ("DOCUMENTO_BAIXADO", "Documento baixado"),
                    ("TRIAGEM_INICIADA", "Triagem iniciada"),
                    ("TRIAGEM_SALVA", "Triagem salva"),
                    ("TRIAGEM_CONCLUIDA", "Triagem concluída"),
                    ("IMPERSONACAO_INICIADA", "Simulação iniciada"),
                    ("IMPERSONACAO_ENCERRADA", "Simulação encerrada"),
                    ("ACAO_BLOQUEADA_IMPERSONACAO", "Ação bloqueada durante simulação"),
                ],
                db_index=True,
                max_length=60,
            ),
        ),
        migrations.AddField(model_name="eventoauditoria", name="recurso", field=models.CharField(blank=True, db_index=True, max_length=120)),
        migrations.AddField(model_name="eventoauditoria", name="objeto_tipo", field=models.CharField(blank=True, db_index=True, max_length=120)),
        migrations.AddField(model_name="eventoauditoria", name="objeto_id", field=models.CharField(blank=True, db_index=True, max_length=100)),
        migrations.AddField(model_name="eventoauditoria", name="objeto_representacao", field=models.CharField(blank=True, max_length=500)),
        migrations.AddField(model_name="eventoauditoria", name="metodo_http", field=models.CharField(blank=True, max_length=10)),
        migrations.AddField(model_name="eventoauditoria", name="caminho", field=models.CharField(blank=True, db_index=True, max_length=500)),
        migrations.AddField(model_name="eventoauditoria", name="status_http", field=models.PositiveSmallIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="eventoauditoria", name="sucesso", field=models.BooleanField(db_index=True, default=True)),
        migrations.AddField(model_name="eventoauditoria", name="campos_alterados", field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name="eventoauditoria", name="dados_anteriores", field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name="eventoauditoria", name="dados_posteriores", field=models.JSONField(blank=True, default=dict)),
        migrations.AddIndex(model_name="eventoauditoria", index=models.Index(fields=["categoria", "created_at"], name="idx_audit_cat_data")),
        migrations.AddIndex(model_name="eventoauditoria", index=models.Index(fields=["objeto_tipo", "objeto_id"], name="idx_audit_objeto")),
    ]
