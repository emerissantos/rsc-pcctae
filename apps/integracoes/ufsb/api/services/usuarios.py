from __future__ import annotations

from apps.integracoes.common.exceptions import (
    IntegrationInvalidResponseError,
    IntegrationNotFoundError,
)
from apps.integracoes.ufsb.oauth.schemas import OAuthUserInfo

from ..client import UFSBApiClient
from ..mappers import map_usuario
from ..schemas import UsuarioInstitucionalDTO


class UsuariosUFSBService:
    def __init__(self, client: UFSBApiClient | None = None):
        self.client = client or UFSBApiClient()

    def resolve_from_userinfo(self, userinfo: OAuthUserInfo) -> UsuarioInstitucionalDTO:
        params: dict[str, object] = {}
        query_params = self.client.config.get("QUERY_PARAMS", {})
        if userinfo.id_usuario is not None:
            params[query_params.get("USUARIO_ID_USUARIO", "id-usuario")] = userinfo.id_usuario
        elif userinfo.login:
            params[query_params.get("USUARIO_LOGIN", "login")] = userinfo.login
        elif userinfo.id_institucional is not None:
            params[
                query_params.get("USUARIO_ID_INSTITUCIONAL", "id-institucional")
            ] = userinfo.id_institucional
        else:
            raise IntegrationInvalidResponseError(
                "Não há identificador suficiente para consultar o usuário institucional."
            )

        result = self.client.get(self.client.config["ENDPOINTS"]["USUARIOS"], params=params)
        payload = result.data
        if isinstance(payload, dict):
            records = [payload]
        elif isinstance(payload, list):
            records = payload
        else:
            raise IntegrationInvalidResponseError()

        usuarios = [map_usuario(item) for item in records if isinstance(item, dict)]
        matching = [item for item in usuarios if self._matches(item, userinfo)]
        if not matching:
            raise IntegrationNotFoundError(
                "A conta autenticada não foi localizada no cadastro institucional de usuários."
            )
        if len(matching) > 1:
            raise IntegrationInvalidResponseError(
                "Mais de uma conta institucional correspondeu à identidade autenticada."
            )
        return matching[0]


    def get_by_identifier(
        self,
        *,
        id_usuario: int | None = None,
        login: str | None = None,
        id_institucional: int | None = None,
    ) -> UsuarioInstitucionalDTO:
        return self.resolve_from_userinfo(
            OAuthUserInfo(
                id_usuario=id_usuario,
                id_institucional=id_institucional,
                login=login,
                nome=None,
                email=None,
                raw={},
            )
        )

    @staticmethod
    def _matches(usuario: UsuarioInstitucionalDTO, userinfo: OAuthUserInfo) -> bool:
        if userinfo.id_usuario is not None:
            return usuario.id_usuario == userinfo.id_usuario
        if userinfo.login:
            return usuario.login.casefold() == userinfo.login.casefold()
        if userinfo.id_institucional is not None:
            return usuario.id_institucional == userinfo.id_institucional
        return False
