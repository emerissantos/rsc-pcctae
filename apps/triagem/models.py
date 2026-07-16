from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import AuditModel, UUIDPublicModel


class ConfiguracaoTriagem(AuditModel):
    class PrazoCorrecao(models.IntegerChoices):
        DEZ = 10, "10 dias"
        TRINTA = 30, "30 dias"
        NOVENTA = 90, "90 dias"

    prazo_correcao_dias = models.PositiveSmallIntegerField(
        choices=PrazoCorrecao.choices,
        default=PrazoCorrecao.TRINTA,
        verbose_name="prazo para correção",
    )

    class Meta:
        verbose_name = "configuração da triagem"
        verbose_name_plural = "configurações da triagem"

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    @classmethod
    def carregar(cls) -> ConfiguracaoTriagem:
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self) -> str:
        return f"Prazo de correção: {self.get_prazo_correcao_dias_display()}"


class ItemChecklistTriagem(UUIDPublicModel, AuditModel):
    codigo = models.CharField(max_length=30, unique=True)
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    ordem = models.PositiveSmallIntegerField(default=0)
    obrigatorio = models.BooleanField(default=True)
    confere_comprovantes = models.BooleanField(
        default=False,
        help_text="Indica que o item exige conferência dos documentos anexados ao requerimento.",
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "item do checklist de triagem"
        verbose_name_plural = "itens do checklist de triagem"
        ordering = ["ordem", "codigo"]

    def __str__(self) -> str:
        return f"{self.codigo} — {self.titulo}"


class TriagemRequerimento(UUIDPublicModel, AuditModel):
    class Resultado(models.TextChoices):
        EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
        APTO = "APTO", "Apto para análise"
        PENDENCIA = "PENDENCIA", "Pendente de correção"

    requerimento = models.ForeignKey(
        "requerimentos.Requerimento",
        on_delete=models.PROTECT,
        related_name="triagens",
    )
    rodada = models.PositiveSmallIntegerField(default=1)
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="triagens_rsc_responsavel",
    )
    resultado = models.CharField(
        max_length=20,
        choices=Resultado.choices,
        default=Resultado.EM_ANDAMENTO,
    )
    iniciada_em = models.DateTimeField(default=timezone.now)
    concluida_em = models.DateTimeField(null=True, blank=True)
    orientacao_correcao = models.TextField(blank=True)
    prazo_correcao_dias_snapshot = models.PositiveSmallIntegerField(null=True, blank=True)
    prazo_correcao_ate = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "triagem de requerimento"
        verbose_name_plural = "triagens de requerimentos"
        ordering = ["-iniciada_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["requerimento", "rodada"],
                name="uniq_triagem_requerimento_rodada",
            ),
            models.CheckConstraint(
                condition=Q(rodada__gt=0),
                name="ck_triagem_rodada_positiva",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.requerimento} — triagem {self.rodada}"

    @property
    def em_andamento(self) -> bool:
        return self.resultado == self.Resultado.EM_ANDAMENTO

    @property
    def possui_pendencia(self) -> bool:
        return self.verificacoes.filter(
            situacao=VerificacaoChecklistTriagem.Situacao.NAO_CONFORME
        ).exists()

    def validar_conclusao(self) -> list[str]:
        erros: list[str] = []
        verificacoes = self.verificacoes.select_related("item")
        if not verificacoes.exists():
            erros.append("A triagem não possui itens de checklist configurados.")
            return erros
        pendentes = verificacoes.filter(
            item_obrigatorio_snapshot=True,
            situacao=VerificacaoChecklistTriagem.Situacao.PENDENTE,
        )
        if pendentes.exists():
            erros.append("Conclua todos os itens obrigatórios do checklist.")
        if self.possui_pendencia and not self.orientacao_correcao.strip():
            erros.append("Informe as orientações para correção das pendências.")
        return erros

    def calcular_prazo_correcao(self, dias: int) -> None:
        self.prazo_correcao_dias_snapshot = dias
        self.prazo_correcao_ate = timezone.localdate() + timedelta(days=dias)


class VerificacaoChecklistTriagem(UUIDPublicModel, AuditModel):
    class Situacao(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        CONFORME = "CONFORME", "Conforme"
        NAO_CONFORME = "NAO_CONFORME", "Não conforme"
        NAO_APLICAVEL = "NAO_APLICAVEL", "Não aplicável"

    triagem = models.ForeignKey(
        TriagemRequerimento,
        on_delete=models.CASCADE,
        related_name="verificacoes",
    )
    item = models.ForeignKey(
        ItemChecklistTriagem,
        on_delete=models.PROTECT,
        related_name="verificacoes",
    )
    item_codigo_snapshot = models.CharField(max_length=30)
    item_titulo_snapshot = models.CharField(max_length=255)
    item_descricao_snapshot = models.TextField(blank=True)
    item_obrigatorio_snapshot = models.BooleanField(default=True)
    item_confere_comprovantes_snapshot = models.BooleanField(default=False)
    situacao = models.CharField(
        max_length=20,
        choices=Situacao.choices,
        default=Situacao.PENDENTE,
    )
    observacao = models.TextField(blank=True)

    class Meta:
        verbose_name = "verificação do checklist"
        verbose_name_plural = "verificações do checklist"
        ordering = ["item__ordem", "item__codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["triagem", "item"],
                name="uniq_verificacao_triagem_item",
            )
        ]

    def clean(self) -> None:
        super().clean()
        if self.situacao == self.Situacao.NAO_CONFORME and not self.observacao.strip():
            raise ValidationError(
                {"observacao": "Descreva a pendência identificada neste item."}
            )

    def save(self, *args, **kwargs):
        if self.item_id and not self.item_codigo_snapshot:
            self.item_codigo_snapshot = self.item.codigo
            self.item_titulo_snapshot = self.item.titulo
            self.item_descricao_snapshot = self.item.descricao
            self.item_obrigatorio_snapshot = self.item.obrigatorio
            self.item_confere_comprovantes_snapshot = self.item.confere_comprovantes
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.triagem} — {self.item_codigo_snapshot or self.item.codigo}"
