from contextvars import ContextVar
from typing import Any

_current_user: ContextVar[Any | None] = ContextVar("current_user", default=None)
_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_current_user(user: Any | None):
    return _current_user.set(user)


def reset_current_user(token) -> None:
    _current_user.reset(token)


def get_current_user() -> Any | None:
    return _current_user.get()


def set_request_id(request_id: str):
    return _request_id.set(request_id)


def reset_request_id(token) -> None:
    _request_id.reset(token)


def get_request_id() -> str | None:
    return _request_id.get()
