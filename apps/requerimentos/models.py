from __future__ import annotations

import hashlib
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from apps.core.models import AuditModel, UUIDPublicModel

CENTAVOS = Decimal("0.01")


class Requerimento(UUIDPublicModel, AuditModel):
    class Situacao(models.TextChoices):
        RASCUNHO = "RASCUNHO", "Rascunho"
        SUBMETIDO = "SUBMETIDO", "Submetido"
        EM_TRIAGEM = "EM_TRIAGEM", "Em triagem"
        PENDENTE_CORRECAO = "PENDENTE_CORRECAO", "Pendente de correção"
        EM_ANALISE = "EM_ANALISE", "Em análise"
        EM_DILIGENCIA = "EM_DILIGENCIA", "Em diligência"
        DEFERIDO = "DEFERIDO", "Deferido"
        INDEFERIDO = "INDEFERIDO", "Indeferido"
        CANCELADO = "CANCELADO", "Cancelado"

    numero = models.CharField(max_length=30, unique=True, null=True, blank=True)
    requerente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requerimentos_rsc",
    )
    vinculo = models.ForeignKey(
        "pessoas.VinculoFuncional",
        on_delete=models.PROTECT,
        related_name="requerimentos_rsc",
    )
    nivel_pretendido = models.ForeignKey(
        "pontuacao.NivelRSC",
        on_delete=models.PROTECT,
        related_name="requerimentos",
    )
    comissao = models.ForeignKey(
        "comissoes.Comissao",
        on_delete=models.PROTECT,
        related_name="requerimentos",
        null=True,
        blank=True,
    )
    situacao = models.CharField(
        max_length=30,
        choices=Situacao.choices,
        default=Situacao.RASCUNHO,
    )
    pontuacao_declarada = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pontuacao_validada = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    submetido_em = models.DateTimeField(null=True, blank=True)
    finalizado_em = models.DateTimeField(null=True, blank=True)
    observacao_geral = models.TextField(blank=True)

    class Meta:
        verbose_name = "requerimento"
        verbose_name_plural = "requerimentos"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["requerente", "situacao"], name="idx_req_usuario_situacao"),
            models.Index(fields=["vinculo", "situacao"], name="idx_req_vinculo_situacao"),
            models.Index(fields=["situacao", "submetido_em"], name="idx_req_situacao_submissao"),
        ]

    def __str__(self) -> str:
        return self.numero or f"Requerimento {self.pk or 'novo'}"

    def get_absolute_url(self) -> str:
        return reverse("requerimentos:detalhe", kwargs={"uuid": self.uuid})

    @property
    def pode_editar(self) -> bool:
        return self.situacao in {self.Situacao.RASCUNHO, self.Situacao.PENDENTE_CORRECAO}

    @property
    def quantidade_itens(self) -> int:
        return self.lancamentos.filter(quantidade_declarada__gt=0).count()

    @property
    def quantidade_documentos(self) -> int:
        return DocumentoLancamento.objects.filter(
            lancamento__requerimento=self,
            ativo=True,
        ).count()

    @property
    def percentual_meta(self) -> Decimal:
        minimo = self.nivel_pretendido.pontuacao_minima
        if not minimo:
            return Decimal("100.00")
        percentual = (self.pontuacao_declarada / minimo) * Decimal("100")
        return min(percentual, Decimal("100.00")).quantize(CENTAVOS)

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating and not self.numero:
            numero = f"RSC-{self.created_at.year}-{self.pk:06d}"
            type(self).objects.filter(pk=self.pk).update(numero=numero)
            self.numero = numero

    def recalcular_pontuacao(self) -> Decimal:
        total = self.lancamentos.aggregate(total=Sum("pontuacao_declarada"))["total"]
        total = (total or Decimal("0.00")).quantize(CENTAVOS)
        type(self).objects.filter(pk=self.pk).update(pontuacao_declarada=total)
        self.pontuacao_declarada = total
        return total

    def validar_submissao(self) -> list[str]:
        erros: list[str] = []
        lancamentos = self.lancamentos.select_related("item").prefetch_related("documentos")
        if not lancamentos.exists():
            erros.append("Informe pelo menos um item de pontuação.")
        for lancamento in lancamentos:
            if (
                lancamento.item_exige_anexo_snapshot
                and not lancamento.documentos.filter(ativo=True).exists()
            ):
                erros.append(f"O item {lancamento.item_codigo_snapshot} precisa de anexo.")
        if self.quantidade_itens < self.nivel_pretendido.quantidade_minima_itens:
            erros.append(
                "O nível pretendido exige ao menos "
                f"{self.nivel_pretendido.quantidade_minima_itens} itens pontuados."
            )
        requisitos_usados = set(
            self.lancamentos.values_list("item__requisito__codigo", flat=True)
        )
        obrigatorios = set(
            self.nivel_pretendido.requisitos_obrigatorios.values_list("codigo", flat=True)
        )
        faltantes = sorted(obrigatorios - requisitos_usados)
        if faltantes:
            erros.append(
                "Inclua ao menos um item dos requisitos obrigatórios: "
                + ", ".join(faltantes)
                + "."
            )
        return erros

    @transaction.atomic
    def submeter(self, usuario=None) -> None:
        if not self.pode_editar:
            raise ValidationError("Este requerimento não pode mais ser submetido.")
        self.recalcular_pontuacao()
        erros = self.validar_submissao()
        if erros:
            raise ValidationError(erros)
        self.situacao = self.Situacao.SUBMETIDO
        self.submetido_em = timezone.now()
        self.updated_by = usuario if getattr(usuario, "is_authenticated", False) else None
        self.save(update_fields=["situacao", "submetido_em", "updated_by", "updated_at"])
        HistoricoRequerimento.objects.create(
            requerimento=self,
            situacao_anterior=self.Situacao.RASCUNHO,
            situacao_nova=self.Situacao.SUBMETIDO,
            descricao="Requerimento submetido pelo servidor.",
            created_by=self.updated_by,
            updated_by=self.updated_by,
        )


class LancamentoItem(UUIDPublicModel, AuditModel):
    class SituacaoValidacao(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        VALIDADO = "VALIDADO", "Validado"
        AJUSTADO = "AJUSTADO", "Ajustado"
        RECUSADO = "RECUSADO", "Recusado"

    requerimento = models.ForeignKey(
        Requerimento,
        on_delete=models.CASCADE,
        related_name="lancamentos",
    )
    item = models.ForeignKey(
        "pontuacao.ItemPontuacao",
        on_delete=models.PROTECT,
        related_name="lancamentos",
    )
    quantidade_declarada = models.DecimalField(max_digits=10, decimal_places=2)
    pontuacao_declarada = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observacao = models.TextField(blank=True)

    item_codigo_snapshot = models.CharField(max_length=20)
    item_descricao_snapshot = models.TextField()
    item_unidade_snapshot = models.CharField(max_length=100)
    item_pontos_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    item_limite_snapshot = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    item_exige_anexo_snapshot = models.BooleanField(default=True)

    quantidade_validada = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    pontuacao_validada = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    situacao_validacao = models.CharField(
        max_length=20,
        choices=SituacaoValidacao.choices,
        default=SituacaoValidacao.PENDENTE,
    )
    justificativa_validacao = models.TextField(blank=True)

    class Meta:
        verbose_name = "lançamento de item"
        verbose_name_plural = "lançamentos de itens"
        ordering = ["item__requisito__ordem", "item__ordem"]
        constraints = [
            models.UniqueConstraint(
                fields=["requerimento", "item"],
                name="uniq_lancamento_requerimento_item",
            ),
            models.CheckConstraint(
                condition=models.Q(quantidade_declarada__gt=0),
                name="ck_lancamento_quantidade_positiva",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.requerimento} — {self.item_codigo_snapshot}"

    def clean(self) -> None:
        super().clean()
        if self.requerimento_id and not self.requerimento.pode_editar:
            raise ValidationError("Não é possível alterar itens deste requerimento.")
        if self.quantidade_declarada is not None and self.quantidade_declarada <= 0:
            raise ValidationError(
                {"quantidade_declarada": "Informe uma quantidade maior que zero."}
            )
        if self.item_id:
            self.item.calcular(self.quantidade_declarada)

    def save(self, *args, **kwargs):
        if not self.item_codigo_snapshot:
            self.item_codigo_snapshot = self.item.codigo
            self.item_descricao_snapshot = self.item.descricao
            self.item_unidade_snapshot = self.item.unidade
            self.item_pontos_snapshot = self.item.pontos_por_quantidade
            self.item_limite_snapshot = self.item.limite_pontos
            self.item_exige_anexo_snapshot = self.item.exige_anexo
        self.pontuacao_declarada = self.item.calcular(self.quantidade_declarada)
        self.full_clean()
        super().save(*args, **kwargs)
        self.requerimento.recalcular_pontuacao()

    def delete(self, *args, **kwargs):
        requerimento = self.requerimento
        if not requerimento.pode_editar:
            raise ValidationError("Não é possível remover itens deste requerimento.")
        result = super().delete(*args, **kwargs)
        requerimento.recalcular_pontuacao()
        return result


def _segmento_caminho(valor, padrao: str) -> str:
    segmento = slugify(str(valor or "").replace(".", "-"), allow_unicode=False).strip("-")
    return segmento[:80] or padrao


def _numero_requerimento_seguro(requerimento: Requerimento) -> str:
    """Retorna o número público do requerimento como segmento seguro de diretório.

    O número é único no banco (por exemplo, ``RSC-2026-000001``), portanto
    identifica de forma estável a pasta do processo sem expor SIAPE, CPF ou
    outros dados funcionais no caminho físico.
    """
    numero = str(requerimento.numero or "").strip().upper()
    seguro = "".join(caractere for caractere in numero if caractere.isalnum() or caractere in "-_")
    return seguro[:80] or f"REQUERIMENTO-{requerimento.uuid.hex}"


def documento_lancamento_upload_to(instance, filename: str) -> str:
    """Organiza comprovantes por requerimento, requisito e item.

    Estrutura:
    ``requerimentos/RSC-2026-000001/requisito-IV/item-IV-2/<uuid>-arquivo.pdf``.

    O número do requerimento é único e o UUID do documento impede colisões,
    inclusive quando usuários enviam arquivos com o mesmo nome original.
    """
    lancamento = instance.lancamento
    requerimento = lancamento.requerimento
    caminho_original = Path(filename)
    extensao = caminho_original.suffix.lower()[:15]
    nome_base = _segmento_caminho(caminho_original.stem, "documento")
    nome_armazenado = f"{instance.uuid.hex}-{nome_base}{extensao}"

    return "/".join(
        [
            "requerimentos",
            _numero_requerimento_seguro(requerimento),
            f"requisito-{_segmento_caminho(lancamento.item.requisito.codigo, 'sem-requisito')}",
            f"item-{_segmento_caminho(lancamento.item.codigo, 'sem-item')}",
            nome_armazenado,
        ]
    )


class DocumentoLancamento(UUIDPublicModel, AuditModel):
    lancamento = models.ForeignKey(
        LancamentoItem,
        on_delete=models.CASCADE,
        related_name="documentos",
    )
    arquivo = models.FileField(
        upload_to=documento_lancamento_upload_to,
        max_length=500,
    )
    nome_original = models.CharField(max_length=255)
    tipo_mime = models.CharField(max_length=150, blank=True)
    tamanho_bytes = models.PositiveBigIntegerField(default=0)
    sha256 = models.CharField(max_length=64, blank=True, db_index=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "documento do item"
        verbose_name_plural = "documentos dos itens"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return self.nome_original

    def save(self, *args, **kwargs):
        if self.lancamento_id and not self.lancamento.requerimento.pode_editar:
            raise ValidationError("Não é possível alterar documentos deste requerimento.")
        if self.arquivo and not self.nome_original:
            self.nome_original = self.arquivo.name.rsplit("/", 1)[-1]
        if self.arquivo and not self.tamanho_bytes:
            self.tamanho_bytes = getattr(self.arquivo, "size", 0)
        if self.arquivo and not self.sha256:
            digest = hashlib.sha256()
            for chunk in self.arquivo.chunks():
                digest.update(chunk)
            self.sha256 = digest.hexdigest()
            try:
                self.arquivo.seek(0)
            except (AttributeError, OSError):
                pass
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        nome_arquivo = self.arquivo.name if self.arquivo else ""
        storage = self.arquivo.storage if self.arquivo else None
        resultado = super().delete(*args, **kwargs)
        if nome_arquivo and storage:
            transaction.on_commit(lambda: storage.delete(nome_arquivo))
        return resultado


class HistoricoRequerimento(UUIDPublicModel, AuditModel):
    requerimento = models.ForeignKey(
        Requerimento,
        on_delete=models.CASCADE,
        related_name="historico",
    )
    situacao_anterior = models.CharField(max_length=30, blank=True)
    situacao_nova = models.CharField(max_length=30)
    descricao = models.TextField()

    class Meta:
        verbose_name = "histórico do requerimento"
        verbose_name_plural = "históricos dos requerimentos"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.requerimento}: {self.situacao_nova}"
