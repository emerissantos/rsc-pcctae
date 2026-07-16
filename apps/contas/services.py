from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.integracoes.common.exceptions import IntegrationAuthorizationError
from apps.integracoes.ufsb.api.services import ServidoresUFSBService, UsuariosUFSBService
from apps.integracoes.ufsb.oauth.schemas import OAuthUserInfo
from apps.pessoas.services import PersistirCadastroInstitucionalService

from .models import IdentidadeExterna, Usuario


@dataclass(frozen=True, slots=True)
class ProvisionResult:
    usuario: Usuario
    identidade: IdentidadeExterna
    vinculos_count: int


class ProvisionarUsuarioUFSBService:
    def __init__(
        self,
        usuarios_service: UsuariosUFSBService | None = None,
        servidores_service: ServidoresUFSBService | None = None,
    ):
        self.usuarios_service = usuarios_service or UsuariosUFSBService()
        self.servidores_service = servidores_service or ServidoresUFSBService()

    def execute(self, *, userinfo: OAuthUserInfo, correlation_id: str = "") -> ProvisionResult:
        usuario_api = self.usuarios_service.resolve_from_userinfo(userinfo)
        if not usuario_api.ativo:
            raise IntegrationAuthorizationError(
                "A conta institucional está inativa e não pode acessar o sistema."
            )
        servidores_api = self.servidores_service.list_by_id_institucional(
            usuario_api.id_institucional
        )
        sync_result = PersistirCadastroInstitucionalService.execute(
            usuario_api=usuario_api,
            servidores_api=servidores_api,
            correlation_id=correlation_id,
        )
        return self._persist_account(
            usuario_api=usuario_api,
            pessoa=sync_result.pessoa,
            vinculos_count=len(sync_result.vinculos),
        )

    @transaction.atomic
    def _persist_account(self, *, usuario_api, pessoa, vinculos_count: int) -> ProvisionResult:
        now = timezone.now()
        identidade = (
            IdentidadeExterna.objects.select_for_update()
            .select_related("usuario")
            .filter(
                provedor="sigauth_ufsb",
                id_usuario_externo=usuario_api.id_usuario,
            )
            .first()
        )

        if identidade:
            usuario = identidade.usuario
        else:
            username = self._available_username(usuario_api.login, usuario_api.id_usuario)
            usuario = Usuario(username=username)
            usuario.set_unusable_password()
            usuario.primeiro_acesso_em = now

        usuario.nome_exibicao = usuario_api.nome_pessoa
        usuario.email = (usuario_api.email or "").lower()
        usuario.first_name = usuario_api.nome_pessoa[:150]
        usuario.is_active = usuario_api.ativo
        usuario.ultimo_acesso_em = now
        usuario.save()

        identidade, _ = IdentidadeExterna.objects.update_or_create(
            provedor="sigauth_ufsb",
            id_usuario_externo=usuario_api.id_usuario,
            defaults={
                "usuario": usuario,
                "pessoa": pessoa,
                "id_institucional": usuario_api.id_institucional,
                "login": usuario_api.login,
                "id_unidade_origem": usuario_api.id_unidade,
                "ativo_na_origem": usuario_api.ativo,
                "email_recebido": usuario_api.email or "",
                "nome_recebido": usuario_api.nome_pessoa,
                "ultimo_login_em": now,
                "ultima_sincronizacao_em": now,
            },
        )
        return ProvisionResult(
            usuario=usuario,
            identidade=identidade,
            vinculos_count=vinculos_count,
        )

    @staticmethod
    def _available_username(login: str, id_usuario: int) -> str:
        base = (login or f"ufsb-{id_usuario}")[:140]
        if not Usuario.objects.filter(username=base).exists():
            return base
        candidate = f"{base[:130]}-{id_usuario}"
        if not Usuario.objects.filter(username=candidate).exists():
            return candidate
        return f"ufsb-{id_usuario}"


class ImportarUsuarioSIGService(ProvisionarUsuarioUFSBService):
    """Importa ou atualiza uma conta sem exigir que a pessoa realize login."""

    def execute(
        self,
        *,
        id_usuario: int | None = None,
        login: str | None = None,
        id_institucional: int | None = None,
        correlation_id: str = "",
    ) -> ProvisionResult:
        usuario_api = self.usuarios_service.get_by_identifier(
            id_usuario=id_usuario,
            login=login,
            id_institucional=id_institucional,
        )
        servidores_api = self.servidores_service.list_by_id_institucional(
            usuario_api.id_institucional
        )
        sync_result = PersistirCadastroInstitucionalService.execute(
            usuario_api=usuario_api,
            servidores_api=servidores_api,
            correlation_id=correlation_id,
        )
        return self._persist_account(
            usuario_api=usuario_api,
            pessoa=sync_result.pessoa,
            vinculos_count=len(sync_result.vinculos),
        )
