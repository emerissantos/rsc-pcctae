from django.db import models

from apps.core.models import TimeStampedModel, UUIDPublicModel


class PessoaInstitucional(TimeStampedModel):
    id_institucional = models.BigIntegerField("ID institucional", unique=True)
    nome = models.CharField(max_length=255)
    nome_identificacao = models.CharField(max_length=255, blank=True)
    email_institucional = models.EmailField(blank=True)
    ativo_na_origem = models.BooleanField(default=True)
    sincronizado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "pessoa institucional"
        verbose_name_plural = "pessoas institucionais"
        ordering = ["nome", "id_institucional"]
        indexes = [models.Index(fields=["nome"], name="idx_pessoa_nome")]

    def __str__(self) -> str:
        return f"{self.nome} ({self.id_institucional})"


class Servidor(TimeStampedModel):
    pessoa = models.OneToOneField(
        PessoaInstitucional,
        on_delete=models.PROTECT,
        related_name="servidor",
    )
    nome_atual = models.CharField(max_length=255)
    nome_identificacao_atual = models.CharField(max_length=255, blank=True)
    email_atual = models.EmailField(blank=True)
    ativo = models.BooleanField(default=True)
    ultima_sincronizacao_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "servidor"
        verbose_name_plural = "servidores"
        ordering = ["nome_atual"]

    def __str__(self) -> str:
        return self.nome_atual


class VinculoFuncional(UUIDPublicModel, TimeStampedModel):
    servidor = models.ForeignKey(
        Servidor,
        on_delete=models.PROTECT,
        related_name="vinculos",
    )
    provedor_origem = models.CharField(max_length=50, default="ufsb_api")
    id_servidor_externo = models.BigIntegerField("ID externo do servidor")
    siape = models.CharField(max_length=20)
    digito_siape = models.CharField(max_length=5, blank=True)
    id_ativo_externo = models.BigIntegerField(null=True, blank=True)
    id_situacao_externa = models.BigIntegerField(null=True, blank=True)
    id_categoria_externa = models.BigIntegerField(null=True, blank=True)
    id_lotacao_externa = models.BigIntegerField(null=True, blank=True)
    lotacao_nome = models.CharField(max_length=255, blank=True)
    id_unidade_exercicio_externa = models.BigIntegerField(null=True, blank=True)
    unidade_exercicio_nome = models.CharField(max_length=255, blank=True)
    id_cargo_externo = models.BigIntegerField(null=True, blank=True)
    cargo_nome = models.CharField(max_length=255, blank=True)
    id_tipo_formacao_externo = models.BigIntegerField(null=True, blank=True)
    regime_trabalho = models.IntegerField(null=True, blank=True)
    data_admissao = models.DateField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    ultima_sincronizacao_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "vínculo funcional"
        verbose_name_plural = "vínculos funcionais"
        ordering = ["-ativo", "siape", "id_servidor_externo"]
        constraints = [
            models.UniqueConstraint(
                fields=["provedor_origem", "id_servidor_externo"],
                name="uniq_vinculo_provedor_servidor",
            )
        ]
        indexes = [
            models.Index(fields=["siape"], name="idx_vinculo_siape"),
            models.Index(fields=["ativo"], name="idx_vinculo_ativo"),
            models.Index(fields=["id_situacao_externa"], name="idx_vinculo_situacao"),
            models.Index(fields=["id_categoria_externa"], name="idx_vinculo_categoria"),
        ]

    def __str__(self) -> str:
        cargo = self.cargo_nome or "Cargo não informado"
        return f"{self.siape} — {cargo}"


class ExecucaoSincronizacao(UUIDPublicModel, TimeStampedModel):
    class Tipo(models.TextChoices):
        USUARIO = "USUARIO", "Usuário"
        SERVIDOR = "SERVIDOR", "Servidor e vínculos"
        COMPLETA = "COMPLETA", "Sincronização completa"

    class Situacao(models.TextChoices):
        INICIADA = "INICIADA", "Iniciada"
        CONCLUIDA = "CONCLUIDA", "Concluída"
        ALERTAS = "ALERTAS", "Concluída com alertas"
        FALHOU = "FALHOU", "Falhou"

    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    pessoa = models.ForeignKey(
        PessoaInstitucional,
        on_delete=models.PROTECT,
        related_name="sincronizacoes",
        null=True,
        blank=True,
    )
    id_institucional_consultado = models.BigIntegerField(null=True, blank=True)
    iniciada_em = models.DateTimeField()
    concluida_em = models.DateTimeField(null=True, blank=True)
    situacao = models.CharField(
        max_length=20,
        choices=Situacao.choices,
        default=Situacao.INICIADA,
    )
    quantidade_recebida = models.PositiveIntegerField(default=0)
    quantidade_criada = models.PositiveIntegerField(default=0)
    quantidade_atualizada = models.PositiveIntegerField(default=0)
    mensagem_resumida = models.CharField(max_length=500, blank=True)
    identificador_correlacao = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        verbose_name = "execução de sincronização"
        verbose_name_plural = "execuções de sincronização"
        ordering = ["-iniciada_em"]
