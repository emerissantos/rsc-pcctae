import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import TimeStampedModel


class Usuario(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nome_exibicao = models.CharField("nome de exibição", max_length=255, blank=True)
    primeiro_acesso_em = models.DateTimeField("primeiro acesso em", null=True, blank=True)
    ultimo_acesso_em = models.DateTimeField("último acesso em", null=True, blank=True)

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"
        ordering = ["username"]
        permissions = [
            ("importar_usuario_sig", "Pode importar usuário do SIG"),
            ("simular_usuario", "Pode simular acesso de outro usuário"),
        ]

    def __str__(self) -> str:
        return self.nome_exibicao or self.get_full_name() or self.username


class IdentidadeExterna(TimeStampedModel):
    pessoa = models.ForeignKey(
        "pessoas.PessoaInstitucional",
        on_delete=models.PROTECT,
        related_name="identidades_externas",
        null=True,
        blank=True,
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="identidades_externas",
    )
    provedor = models.CharField(max_length=50, default="sigauth_ufsb")
    id_usuario_externo = models.BigIntegerField("ID do usuário externo")
    id_institucional = models.BigIntegerField("ID institucional", null=True, blank=True)
    login = models.CharField(max_length=150)
    id_unidade_origem = models.BigIntegerField(null=True, blank=True)
    ativo_na_origem = models.BooleanField(default=True)
    email_recebido = models.EmailField(blank=True)
    nome_recebido = models.CharField(max_length=255, blank=True)
    ultimo_login_em = models.DateTimeField(null=True, blank=True)
    ultima_sincronizacao_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "identidade externa"
        verbose_name_plural = "identidades externas"
        ordering = ["provedor", "login"]
        constraints = [
            models.UniqueConstraint(
                fields=["provedor", "id_usuario_externo"],
                name="uniq_identidade_provedor_usuario",
            ),
        ]
        indexes = [
            models.Index(fields=["id_institucional"], name="idx_identidade_institucional"),
            models.Index(fields=["login"], name="idx_identidade_login"),
        ]

    def __str__(self) -> str:
        return f"{self.provedor}:{self.login}"
