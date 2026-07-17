from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel, UUIDPublicModel


class EventoAuditoria(UUIDPublicModel, TimeStampedModel):
    class Categoria(models.TextChoices):
        AUTENTICACAO = "AUTENTICACAO", "Autenticação"
        ACESSO = "ACESSO", "Acesso e autorização"
        CADASTRO = "CADASTRO", "Cadastro estrutural"
        REQUERIMENTO = "REQUERIMENTO", "Requerimento"
        DOCUMENTO = "DOCUMENTO", "Documento"
        TRIAGEM = "TRIAGEM", "Triagem"
        IMPERSONACAO = "IMPERSONACAO", "Simulação de usuário"
        INTEGRACAO = "INTEGRACAO", "Integração institucional"

    class Nivel(models.TextChoices):
        INFORMATIVO = "INFORMATIVO", "Informativo"
        ATENCAO = "ATENCAO", "Atenção"
        CRITICO = "CRITICO", "Crítico"

    class Tipo(models.TextChoices):
        LOGIN_SUCESSO = "LOGIN_SUCESSO", "Login realizado"
        LOGIN_FALHA = "LOGIN_FALHA", "Falha de login"
        LOGOUT = "LOGOUT", "Logout realizado"
        ACESSO_NEGADO = "ACESSO_NEGADO", "Acesso negado"
        REQUERIMENTO_VISUALIZADO = "REQUERIMENTO_VISUALIZADO", "Requerimento visualizado"
        IMPORTACAO_USUARIO_SIG = "IMPORTACAO_USUARIO_SIG", "Importação de usuário do SIG"
        CADASTRO_CRIADO = "CADASTRO_CRIADO", "Cadastro criado"
        CADASTRO_ALTERADO = "CADASTRO_ALTERADO", "Cadastro alterado"
        CADASTRO_EXCLUIDO = "CADASTRO_EXCLUIDO", "Cadastro excluído"
        REQUERIMENTO_CRIADO = "REQUERIMENTO_CRIADO", "Requerimento criado"
        ITEM_REQUERIMENTO_SALVO = "ITEM_REQUERIMENTO_SALVO", "Item do requerimento salvo"
        ITEM_REQUERIMENTO_REMOVIDO = (
            "ITEM_REQUERIMENTO_REMOVIDO",
            "Item do requerimento removido",
        )
        REQUERIMENTO_SUBMETIDO = "REQUERIMENTO_SUBMETIDO", "Requerimento submetido"
        UPLOAD_TEMPORARIO_CRIADO = "UPLOAD_TEMPORARIO_CRIADO", "Upload temporário criado"
        UPLOAD_TEMPORARIO_REMOVIDO = (
            "UPLOAD_TEMPORARIO_REMOVIDO",
            "Upload temporário removido",
        )
        DOCUMENTO_ADICIONADO = "DOCUMENTO_ADICIONADO", "Documento adicionado"
        DOCUMENTO_REMOVIDO = "DOCUMENTO_REMOVIDO", "Documento removido"
        DOCUMENTO_BAIXADO = "DOCUMENTO_BAIXADO", "Documento baixado"
        FORMULARIO_F00_GERADO = "FORMULARIO_F00_GERADO", "Formulário F-00 gerado"
        TRIAGEM_INICIADA = "TRIAGEM_INICIADA", "Triagem iniciada"
        TRIAGEM_SALVA = "TRIAGEM_SALVA", "Triagem salva"
        TRIAGEM_CONCLUIDA = "TRIAGEM_CONCLUIDA", "Triagem concluída"
        IMPERSONACAO_INICIADA = "IMPERSONACAO_INICIADA", "Simulação iniciada"
        IMPERSONACAO_ENCERRADA = "IMPERSONACAO_ENCERRADA", "Simulação encerrada"
        ACAO_BLOQUEADA_IMPERSONACAO = (
            "ACAO_BLOQUEADA_IMPERSONACAO",
            "Ação bloqueada durante simulação",
        )

    categoria = models.CharField(
        max_length=30,
        choices=Categoria.choices,
        default=Categoria.ACESSO,
        db_index=True,
    )
    nivel = models.CharField(
        max_length=20,
        choices=Nivel.choices,
        default=Nivel.INFORMATIVO,
        db_index=True,
    )
    tipo = models.CharField(max_length=60, choices=Tipo.choices, db_index=True)
    ator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="eventos_auditoria_realizados",
        null=True,
        blank=True,
    )
    usuario_afetado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="eventos_auditoria_recebidos",
        null=True,
        blank=True,
    )
    descricao = models.CharField(max_length=500)
    recurso = models.CharField(max_length=120, blank=True, db_index=True)
    objeto_tipo = models.CharField(max_length=120, blank=True, db_index=True)
    objeto_id = models.CharField(max_length=100, blank=True, db_index=True)
    objeto_representacao = models.CharField(max_length=500, blank=True)
    metodo_http = models.CharField(max_length=10, blank=True)
    caminho = models.CharField(max_length=500, blank=True, db_index=True)
    status_http = models.PositiveSmallIntegerField(null=True, blank=True)
    sucesso = models.BooleanField(default=True, db_index=True)
    campos_alterados = models.JSONField(default=list, blank=True)
    dados_anteriores = models.JSONField(default=dict, blank=True)
    dados_posteriores = models.JSONField(default=dict, blank=True)
    dados = models.JSONField(default=dict, blank=True)
    request_id = models.CharField(max_length=64, blank=True, db_index=True)
    endereco_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = "evento de auditoria"
        verbose_name_plural = "eventos de auditoria"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tipo", "created_at"], name="idx_audit_tipo_data"),
            models.Index(fields=["categoria", "created_at"], name="idx_audit_cat_data"),
            models.Index(fields=["objeto_tipo", "objeto_id"], name="idx_audit_objeto"),
        ]

    def __str__(self) -> str:
        data = self.created_at.strftime("%d/%m/%Y %H:%M") if self.created_at else "novo"
        return f"{self.get_tipo_display()} — {data}"


class SessaoImpersonacao(UUIDPublicModel, TimeStampedModel):
    ator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sessoes_impersonacao_iniciadas",
    )
    usuario_simulado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sessoes_em_que_foi_simulado",
    )
    justificativa = models.CharField(max_length=500)
    iniciada_em = models.DateTimeField(default=timezone.now, db_index=True)
    encerrada_em = models.DateTimeField(null=True, blank=True, db_index=True)
    encerrada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sessoes_impersonacao_encerradas",
        null=True,
        blank=True,
    )
    motivo_encerramento = models.CharField(max_length=250, blank=True)
    request_id_inicio = models.CharField(max_length=64, blank=True, db_index=True)
    endereco_ip_inicio = models.GenericIPAddressField(null=True, blank=True)
    user_agent_inicio = models.CharField(max_length=500, blank=True)

    class Meta:
        verbose_name = "sessão de simulação de usuário"
        verbose_name_plural = "sessões de simulação de usuário"
        ordering = ["-iniciada_em"]
        indexes = [
            models.Index(fields=["ator", "encerrada_em"], name="idx_imp_ator_ativa"),
            models.Index(
                fields=["usuario_simulado", "iniciada_em"],
                name="idx_imp_alvo_data",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["ator"],
                condition=models.Q(encerrada_em__isnull=True),
                name="uniq_impersonacao_ativa_ator",
            )
        ]

    @property
    def ativa(self) -> bool:
        return self.encerrada_em is None

    def encerrar(self, *, usuario=None, motivo: str = "") -> None:
        if self.encerrada_em is not None:
            return
        self.encerrada_em = timezone.now()
        self.encerrada_por = usuario
        self.motivo_encerramento = motivo[:250]
        self.save(
            update_fields=[
                "encerrada_em",
                "encerrada_por",
                "motivo_encerramento",
                "updated_at",
            ]
        )

    def __str__(self) -> str:
        return f"{self.ator} simulando {self.usuario_simulado}"
