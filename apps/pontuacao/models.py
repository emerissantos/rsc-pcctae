from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.core.models import AuditModel, UUIDPublicModel

CENTAVOS = Decimal("0.01")


class Requisito(UUIDPublicModel, AuditModel):
    codigo = models.CharField(max_length=10, unique=True)
    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    ordem = models.PositiveSmallIntegerField(default=1)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "requisito"
        verbose_name_plural = "requisitos"
        ordering = ["ordem", "codigo"]
        indexes = [models.Index(fields=["ativo", "ordem"], name="idx_req_ativo_ordem")]

    def __str__(self) -> str:
        return f"Requisito {self.codigo} — {self.nome}"


class ItemPontuacao(UUIDPublicModel, AuditModel):
    class TipoQuantidade(models.TextChoices):
        INTEIRA = "INTEIRA", "Número inteiro"
        DECIMAL = "DECIMAL", "Número decimal"

    requisito = models.ForeignKey(
        Requisito,
        on_delete=models.PROTECT,
        related_name="itens",
    )
    codigo = models.CharField(max_length=20, unique=True)
    descricao = models.TextField()
    unidade = models.CharField(max_length=100)
    pontos_por_quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    limite_pontos = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    tipo_quantidade = models.CharField(
        max_length=10,
        choices=TipoQuantidade.choices,
        default=TipoQuantidade.INTEIRA,
    )
    exige_anexo = models.BooleanField(default=True)
    observacao_permitida = models.BooleanField(default=True)
    orientacao = models.TextField(blank=True)
    ordem = models.PositiveSmallIntegerField(default=1)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "item de pontuação"
        verbose_name_plural = "itens de pontuação"
        ordering = ["requisito__ordem", "ordem", "codigo"]
        constraints = [
            models.CheckConstraint(
                condition=Q(pontos_por_quantidade__gte=0),
                name="ck_item_pontos_nao_negativos",
            ),
            models.CheckConstraint(
                condition=Q(limite_pontos__isnull=True) | Q(limite_pontos__gte=0),
                name="ck_item_limite_nao_negativo",
            ),
        ]
        indexes = [
            models.Index(fields=["requisito", "ativo"], name="idx_item_req_ativo"),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} — {self.descricao[:80]}"

    def clean(self) -> None:
        super().clean()
        if self.pontos_por_quantidade is not None and self.pontos_por_quantidade < 0:
            raise ValidationError({"pontos_por_quantidade": "A pontuação não pode ser negativa."})

    def calcular(self, quantidade: Decimal | int | str) -> Decimal:
        quantidade_decimal = Decimal(str(quantidade))
        if quantidade_decimal < 0:
            raise ValidationError("A quantidade não pode ser negativa.")
        if self.tipo_quantidade == self.TipoQuantidade.INTEIRA:
            if quantidade_decimal != quantidade_decimal.to_integral_value():
                raise ValidationError("Este item aceita somente quantidade inteira.")
        total = quantidade_decimal * self.pontos_por_quantidade
        if self.limite_pontos is not None:
            total = min(total, self.limite_pontos)
        return total.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


class NivelRSC(UUIDPublicModel, AuditModel):
    codigo = models.CharField(max_length=10, unique=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    pontuacao_minima = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade_minima_itens = models.PositiveSmallIntegerField(default=1)
    ordem = models.PositiveSmallIntegerField(default=1)
    ativo = models.BooleanField(default=True)
    requisitos_obrigatorios = models.ManyToManyField(
        Requisito,
        through="NivelRequisitoObrigatorio",
        related_name="niveis_obrigatorios",
        blank=True,
    )

    class Meta:
        verbose_name = "nível de RSC"
        verbose_name_plural = "níveis de RSC"
        ordering = ["ordem", "codigo"]
        constraints = [
            models.CheckConstraint(
                condition=Q(pontuacao_minima__gte=0),
                name="ck_nivel_pontos_nao_negativos",
            )
        ]

    def __str__(self) -> str:
        return self.nome


class NivelRequisitoObrigatorio(AuditModel):
    nivel = models.ForeignKey(NivelRSC, on_delete=models.CASCADE)
    requisito = models.ForeignKey(Requisito, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "requisito obrigatório do nível"
        verbose_name_plural = "requisitos obrigatórios dos níveis"
        constraints = [
            models.UniqueConstraint(
                fields=["nivel", "requisito"],
                name="uniq_nivel_requisito_obrigatorio",
            )
        ]

    def __str__(self) -> str:
        return f"{self.nivel.codigo}: requisito {self.requisito.codigo}"
