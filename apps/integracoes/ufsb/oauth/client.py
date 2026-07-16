from __future__ import annotations

import hashlib
import logging
import secrets
from base64 import urlsafe_b64encode
from typing import Any
from urllib.parse import urlencode

import requests
from django.conf import settings

from apps.integracoes.common.exceptions import (
    IntegrationAuthenticationError,
    IntegrationConfigurationError,
    IntegrationInvalidResponseError,
    IntegrationTimeoutError,
)

from .schemas import OAuthToken, OAuthUserInfo

logger = logging.getLogger(__name__)


def _first_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value not in (None, ""):
            return value
    return None


def _to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class UFSBOAuthClient:
    """Cliente do fluxo OAuth2 Authorization Code da UFSB."""

    def __init__(self, session: requests.Session | None = None):
        self.config = settings.UFSB_AUTH
        self.session = session or requests.Session()

    def validate_configuration(self) -> None:
        required = {
            "CLIENT_ID": self.config.get("CLIENT_ID"),
            "CLIENT_SECRET": self.config.get("CLIENT_SECRET"),
            "AUTHORIZATION_URL": self.config.get("AUTHORIZATION_URL"),
            "TOKEN_URL": self.config.get("TOKEN_URL"),
            "USERINFO_URL": self.config.get("USERINFO_URL"),
            "REDIRECT_URI": self.config.get("REDIRECT_URI"),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            logger.error("oauth_configuration_missing", extra={"missing": missing})
            raise IntegrationConfigurationError()

    @staticmethod
    def generate_state() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_pkce_verifier() -> str:
        return secrets.token_urlsafe(64)

    @staticmethod
    def pkce_challenge(verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        return urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    def build_authorization_url(self, *, state: str, code_verifier: str | None = None) -> str:
        self.validate_configuration()
        params: dict[str, str] = {
            "response_type": "code",
            "client_id": self.config["CLIENT_ID"],
            "redirect_uri": self.config["REDIRECT_URI"],
            "scope": self.config.get("SCOPE", "read"),
            "state": state,
        }
        if code_verifier:
            params.update(
                {
                    "code_challenge": self.pkce_challenge(code_verifier),
                    "code_challenge_method": "S256",
                }
            )
        return f"{self.config['AUTHORIZATION_URL']}?{urlencode(params)}"

    def exchange_code(self, *, code: str, code_verifier: str | None = None) -> OAuthToken:
        self.validate_configuration()
        data: dict[str, str] = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.config["REDIRECT_URI"],
        }
        if code_verifier:
            data["code_verifier"] = code_verifier

        auth_method = self.config.get("TOKEN_AUTH_METHOD", "client_secret_basic")
        request_kwargs: dict[str, Any] = {}
        if auth_method == "client_secret_post":
            data["client_id"] = self.config["CLIENT_ID"]
            data["client_secret"] = self.config["CLIENT_SECRET"]
        else:
            request_kwargs["auth"] = (
                self.config["CLIENT_ID"],
                self.config["CLIENT_SECRET"],
            )

        try:
            response = self.session.post(
                self.config["TOKEN_URL"],
                data=data,
                headers={"Accept": "application/json"},
                timeout=self._timeout(),
                verify=self._verify(),
                **request_kwargs,
            )
        except requests.Timeout as exc:
            raise IntegrationTimeoutError() from exc
        except requests.RequestException as exc:
            logger.exception("oauth_token_request_failed")
            raise IntegrationAuthenticationError() from exc

        if response.status_code >= 400:
            logger.warning(
                "oauth_token_rejected",
                extra={"status_code": response.status_code},
            )
            raise IntegrationAuthenticationError(status_code=response.status_code)

        try:
            payload = response.json()
        except ValueError as exc:
            raise IntegrationInvalidResponseError(status_code=response.status_code) from exc

        access_token = payload.get("access_token")
        if not access_token:
            raise IntegrationInvalidResponseError(status_code=response.status_code)

        return OAuthToken(
            access_token=str(access_token),
            token_type=str(payload.get("token_type") or "Bearer"),
            expires_in=_to_int(payload.get("expires_in")),
            scope=payload.get("scope"),
        )

    def fetch_user_info(self, token: OAuthToken) -> OAuthUserInfo:
        headers = {
            "Authorization": f"{token.token_type} {token.access_token}",
            "Accept": "application/json",
        }
        userinfo_api_key = self.config.get("USERINFO_API_KEY")
        if userinfo_api_key:
            headers["x-api-key"] = userinfo_api_key

        try:
            response = self.session.get(
                self.config["USERINFO_URL"],
                headers=headers,
                timeout=self._timeout(),
                verify=self._verify(),
            )
        except requests.Timeout as exc:
            raise IntegrationTimeoutError() from exc
        except requests.RequestException as exc:
            logger.exception("oauth_userinfo_request_failed")
            raise IntegrationAuthenticationError() from exc

        if response.status_code >= 400:
            logger.warning(
                "oauth_userinfo_rejected",
                extra={"status_code": response.status_code},
            )
            raise IntegrationAuthenticationError(status_code=response.status_code)

        try:
            payload = response.json()
        except ValueError as exc:
            raise IntegrationInvalidResponseError(status_code=response.status_code) from exc

        if not isinstance(payload, dict):
            raise IntegrationInvalidResponseError(status_code=response.status_code)

        return self.normalize_user_info(payload)

    def normalize_user_info(self, payload: dict[str, Any]) -> OAuthUserInfo:
        attribute = self.config.get("USER_NAME_ATTRIBUTE", "pessoa")
        nested = payload.get(attribute)
        candidate: dict[str, Any] = payload
        if isinstance(nested, dict):
            candidate = {**payload, **nested}

        id_usuario = _to_int(
            _first_value(candidate, "id-usuario", "id_usuario", "idUsuario", "user_id")
        )
        id_institucional = _to_int(
            _first_value(
                candidate,
                "id-institucional",
                "id_institucional",
                "idInstitucional",
                "institutional_id",
            )
        )
        login = _first_value(
            candidate,
            "login",
            "username",
            "preferred_username",
            "usuario",
        )
        if id_institucional is None and isinstance(nested, int):
            id_institucional = nested
        if not login and isinstance(nested, str):
            if nested.isdigit() and id_institucional is None:
                id_institucional = int(nested)
            else:
                login = nested

        nome = _first_value(candidate, "nome-pessoa", "nome", "name", "display_name")
        email = _first_value(candidate, "email", "mail")

        if id_usuario is None and not login and id_institucional is None:
            raise IntegrationInvalidResponseError(
                "O endpoint de usuário autenticado não retornou um identificador utilizável."
            )

        return OAuthUserInfo(
            id_usuario=id_usuario,
            id_institucional=id_institucional,
            login=str(login) if login else None,
            nome=str(nome) if nome else None,
            email=str(email) if email else None,
            raw=payload,
        )

    def _timeout(self) -> tuple[int, int]:
        return (
            int(self.config.get("CONNECT_TIMEOUT_SECONDS", 3)),
            int(self.config.get("TIMEOUT_SECONDS", 10)),
        )

    def _verify(self) -> bool | str:
        return self.config.get("CA_BUNDLE") or bool(self.config.get("VERIFY_SSL", True))
