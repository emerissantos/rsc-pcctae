from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.core.models import AuditModel, UUIDPublicModel


class Comissao(UUIDPublicModel, AuditModel):
    nome = models.CharField(max_length=255)
    sigla = models.CharField(max_length=30, blank=True)
    ato_designacao = models.CharField(max_length=150, blank=True)
    inicio_vigencia = models.DateField()
    fim_vigencia = models.DateField(null=True, blank=True)
    ativa = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = "comissão"
        verbose_name_plural = "comissões"
        ordering = ["-ativa", "-inicio_vigencia", "nome"]
        constraints = [
            models.CheckConstraint(
                condition=Q(fim_vigencia__isnull=True)
                | Q(fim_vigencia__gte=models.F("inicio_vigencia")),
                name="ck_comissao_vigencia_valida",
            )
        ]

    def __str__(self) -> str:
        return self.sigla or self.nome


class MembroComissao(UUIDPublicModel, AuditModel):
    class Papel(models.TextChoices):
        PRESIDENTE = "PRESIDENTE", "Presidente"
        VICE_PRESIDENTE = "VICE_PRESIDENTE", "Vice-presidente"
        MEMBRO = "MEMBRO", "Membro"
        SECRETARIA = "SECRETARIA", "Secretaria"

    comissao = models.ForeignKey(
        Comissao,
        on_delete=models.PROTECT,
        related_name="membros",
    )
    usuario = models.ForeignKey(
        "contas.Usuario",
        on_delete=models.PROTECT,
        related_name="participacoes_comissoes",
        null=True,
        blank=True,
    )
    nome_snapshot = models.CharField(max_length=255)
    email_snapshot = models.EmailField(blank=True)
    papel = models.CharField(max_length=30, choices=Papel.choices, default=Papel.MEMBRO)
    inicio_mandato = models.DateField()
    fim_mandato = models.DateField(null=True, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "membro da comissão"
        verbose_name_plural = "membros da comissão"
        ordering = ["comissao", "papel", "nome_snapshot"]
        constraints = [
            models.CheckConstraint(
                condition=Q(fim_mandato__isnull=True)
                | Q(fim_mandato__gte=models.F("inicio_mandato")),
                name="ck_membro_mandato_valido",
            )
        ]

    def clean(self) -> None:
        super().clean()
        if self.usuario_id and not self.nome_snapshot:
            self.nome_snapshot = str(self.usuario)
        if self.usuario_id and not self.email_snapshot:
            self.email_snapshot = self.usuario.email
        if self.fim_mandato and self.fim_mandato < self.inicio_mandato:
            raise ValidationError({"fim_mandato": "O fim do mandato não pode anteceder o início."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.nome_snapshot} — {self.get_papel_display()}"
