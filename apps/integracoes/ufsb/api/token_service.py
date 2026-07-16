from __future__ import annotations

import logging
import time
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache

from apps.integracoes.common.exceptions import (
    IntegrationAuthenticationError,
    IntegrationConfigurationError,
    IntegrationInvalidResponseError,
    IntegrationTimeoutError,
)

logger = logging.getLogger(__name__)


class UFSBTechnicalTokenService:
    CACHE_KEY = "integracoes:ufsb:technical-token:v1"

    def __init__(self, session: requests.Session | None = None):
        self.config = settings.UFSB_API
        self.session = session or requests.Session()

    def get_access_token(self, *, force_refresh: bool = False) -> str:
        if not force_refresh:
            cached = cache.get(self.CACHE_KEY)
            if isinstance(cached, dict) and cached.get("access_token"):
                return str(cached["access_token"])

        self._validate_configuration()
        data: dict[str, str] = {"grant_type": "client_credentials"}
        scope = self.config.get("SCOPE")
        if scope:
            data["scope"] = scope

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
            logger.exception("ufsb_technical_token_request_failed")
            raise IntegrationAuthenticationError() from exc

        if response.status_code >= 400:
            logger.warning(
                "ufsb_technical_token_rejected",
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

        try:
            expires_in = max(int(payload.get("expires_in", 300)), 30)
        except (TypeError, ValueError):
            expires_in = 300
        safety_margin = min(60, max(10, expires_in // 10))
        timeout = max(expires_in - safety_margin, 10)
        cache.set(
            self.CACHE_KEY,
            {"access_token": access_token, "cached_at": int(time.time())},
            timeout=timeout,
        )
        return str(access_token)

    def invalidate(self) -> None:
        cache.delete(self.CACHE_KEY)

    def _validate_configuration(self) -> None:
        required = ("CLIENT_ID", "CLIENT_SECRET", "API_KEY", "TOKEN_URL")
        if any(not self.config.get(key) for key in required):
            raise IntegrationConfigurationError()

    def _timeout(self) -> tuple[int, int]:
        return (
            int(self.config.get("CONNECT_TIMEOUT_SECONDS", 3)),
            int(self.config.get("TIMEOUT_SECONDS", 10)),
        )

    def _verify(self) -> bool | str:
        return self.config.get("CA_BUNDLE") or bool(self.config.get("VERIFY_SSL", True))
