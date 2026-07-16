from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

import requests
from django.conf import settings

from apps.integracoes.common.exceptions import (
    IntegrationAuthenticationError,
    IntegrationAuthorizationError,
    IntegrationInvalidResponseError,
    IntegrationNotFoundError,
    IntegrationRateLimitError,
    IntegrationTimeoutError,
)

from .schemas import APIResult, PageMetadata, RateLimitMetadata
from .token_service import UFSBTechnicalTokenService

logger = logging.getLogger(__name__)


def _header_int(headers: requests.structures.CaseInsensitiveDict, *names: str) -> int | None:
    for name in names:
        value = headers.get(name)
        if value not in (None, ""):
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
    return None


class UFSBApiClient:
    def __init__(
        self,
        session: requests.Session | None = None,
        token_service: UFSBTechnicalTokenService | None = None,
    ):
        self.config = settings.UFSB_API
        self.session = session or requests.Session()
        self.token_service = token_service or UFSBTechnicalTokenService(self.session)

    def get(self, url: str, *, params: dict[str, Any] | None = None) -> APIResult:
        return self._request("GET", url, params=params)

    def iter_pages(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        page_param: str | None = None,
        start_page: int = 0,
    ) -> Iterator[APIResult]:
        current = start_page
        page_name = page_param or self.config.get("PAGE_PARAM", "page")
        base_params = dict(params or {})
        while True:
            page_params = {**base_params, page_name: current}
            result = self.get(url, params=page_params)
            yield result
            pages = result.page.pages
            if pages is None or current + 1 >= pages:
                break
            current += 1

    def _request(self, method: str, url: str, **kwargs: Any) -> APIResult:
        if not url:
            raise IntegrationInvalidResponseError("Endpoint institucional não configurado.")

        response = None
        for attempt in range(2):
            token = self.token_service.get_access_token(force_refresh=attempt == 1)
            headers = {
                "Authorization": f"Bearer {token}",
                "x-api-key": self.config["API_KEY"],
                "Content-Type": "application/json;charset=UTF-8",
                "Accept": "application/json",
            }
            extra_headers = kwargs.get("headers", {})
            headers.update(extra_headers)
            request_kwargs = {key: value for key, value in kwargs.items() if key != "headers"}

            try:
                response = self.session.request(
                    method,
                    url,
                    headers=headers,
                    timeout=self._timeout(),
                    verify=self._verify(),
                    **request_kwargs,
                )
            except requests.Timeout as exc:
                raise IntegrationTimeoutError() from exc
            except requests.RequestException as exc:
                logger.exception("ufsb_api_request_failed", extra={"endpoint": url})
                raise IntegrationInvalidResponseError() from exc

            if response.status_code == 401 and attempt == 0:
                self.token_service.invalidate()
                continue
            break

        if response is None:
            raise IntegrationInvalidResponseError()
        if response.status_code == 401:
            raise IntegrationAuthenticationError(status_code=401)
        if response.status_code == 403:
            raise IntegrationAuthorizationError(status_code=403)
        if response.status_code == 404:
            raise IntegrationNotFoundError(status_code=404)
        if response.status_code == 429:
            raise IntegrationRateLimitError(
                status_code=429,
                reset_seconds=_header_int(response.headers, "Retry-After", "RateLimit-Reset"),
            )
        if response.status_code >= 400:
            logger.warning(
                "ufsb_api_error",
                extra={"endpoint": url, "status_code": response.status_code},
            )
            raise IntegrationInvalidResponseError(status_code=response.status_code)

        try:
            data = response.json()
        except ValueError as exc:
            raise IntegrationInvalidResponseError(status_code=response.status_code) from exc

        page = PageMetadata(
            pages=_header_int(response.headers, "X-Pages"),
            total=_header_int(response.headers, "X-Total"),
        )
        rate_limit = RateLimitMetadata(
            limit=_header_int(
                response.headers,
                "X-RateLimit-Limit-Hour",
                "RateLimit-Limit",
            ),
            remaining=_header_int(
                response.headers,
                "X-RateLimit-Remaining-Hour",
                "RateLimit-Remaining",
            ),
            reset_seconds=_header_int(response.headers, "RateLimit-Reset"),
        )
        self._log_rate_limit(url, rate_limit)
        return APIResult(
            data=data,
            page=page,
            rate_limit=rate_limit,
            status_code=response.status_code,
        )

    def _log_rate_limit(self, url: str, metadata: RateLimitMetadata) -> None:
        if not metadata.limit or metadata.remaining is None:
            return
        remaining_percent = (metadata.remaining / metadata.limit) * 100
        if remaining_percent <= int(self.config.get("RATE_LIMIT_ALERT_PERCENT", 10)):
            logger.warning(
                "ufsb_api_rate_limit_low",
                extra={
                    "endpoint": url,
                    "rate_limit_remaining": metadata.remaining,
                    "rate_limit_limit": metadata.limit,
                    "rate_limit_reset": metadata.reset_seconds,
                },
            )

    def _timeout(self) -> tuple[int, int]:
        return (
            int(self.config.get("CONNECT_TIMEOUT_SECONDS", 3)),
            int(self.config.get("TIMEOUT_SECONDS", 10)),
        )

    def _verify(self) -> bool | str:
        return self.config.get("CA_BUNDLE") or bool(self.config.get("VERIFY_SSL", True))
