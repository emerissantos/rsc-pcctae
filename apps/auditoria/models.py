from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel, UUIDPublicModel


class EventoAuditoria(UUIDPublicModel, TimeStampedModel):
    class Tipo(models.TextChoices):
        IMPORTACAO_USUARIO_SIG = "IMPORTACAO_USUARIO_SIG", "Importação de usuário do SIG"
        ACAO_BLOQUEADA_IMPERSONACAO = (
            "ACAO_BLOQUEADA_IMPERSONACAO",
            "Ação bloqueada durante simulação",
        )

    tipo = models.CharField(max_length=50, choices=Tipo.choices, db_index=True)
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
        ]

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} — {self.created_at:%d/%m/%Y %H:%M}"


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
