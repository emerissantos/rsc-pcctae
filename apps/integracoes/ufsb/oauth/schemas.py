from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class OAuthToken:
    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    scope: str | None = None


@dataclass(frozen=True, slots=True)
class OAuthUserInfo:
    id_usuario: int | None
    id_institucional: int | None
    login: str | None
    nome: str | None
    email: str | None
    raw: dict[str, Any]

    @property
    def has_stable_account_id(self) -> bool:
        return self.id_usuario is not None
