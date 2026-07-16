import json
import logging
import re
from datetime import UTC, datetime

from .context import get_current_user, get_request_id

SENSITIVE_KEYS = {
    "password",
    "token",
    "access_token",
    "refresh_token",
    "client_secret",
    "api_key",
    "x-api-key",
    "authorization",
    "cpf",
    "cpf-cnpj",
}

SENSITIVE_QUERY_PATTERN = re.compile(
    r"(?i)(code|state|access_token|refresh_token|client_secret|api_key|x-api-key)=([^&\s\"']+)"
)
BEARER_PATTERN = re.compile(r"(?i)Bearer\s+[A-Za-z0-9._~+\-/]+=*")


def sanitize_text(value: str) -> str:
    value = SENSITIVE_QUERY_PATTERN.sub(r"\1=***", value)
    return BEARER_PATTERN.sub("Bearer ***", value)


def sanitize(value):
    if isinstance(value, dict):
        return {
            key: "***" if key.lower() in SENSITIVE_KEYS else sanitize(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    if isinstance(value, str):
        return sanitize_text(value)
    return value


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        user = get_current_user()
        record.request_id = get_request_id()
        record.user_id = getattr(user, "pk", None)
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "user_id": getattr(record, "user_id", None),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(sanitize(payload), ensure_ascii=False, default=str)
