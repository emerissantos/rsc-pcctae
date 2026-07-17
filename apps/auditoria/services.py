from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from ipaddress import ip_address
from pathlib import Path
from typing import Any
from uuid import UUID

from django.db import models
from django.db.models.fields.files import FieldFile

from .models import EventoAuditoria

SENSITIVE_FIELD_PARTS = (
    "password",
    "senha",
    "token",
    "secret",
    "api_key",
    "apikey",
    "authorization",
)
MASKED_FIELD_PARTS = ("cpf", "cnpj")
MAX_TEXT_LENGTH = 2000


def get_client_ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    candidates = [
        forwarded.split(",", 1)[0].strip() if forwarded else "",
        request.META.get("HTTP_X_REAL_IP", "").strip(),
        request.META.get("REMOTE_ADDR", "").strip(),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return str(ip_address(candidate))
        except ValueError:
            continue
    return None


def _mask_identifier(value: Any) -> str:
    text = "" if value is None else str(value)
    if len(text) <= 4:
        return "***"
    return f"***{text[-4:]}"


def normalizar_valor(value: Any, *, field_name: str = "") -> Any:
    lower_name = field_name.lower()
    if any(part in lower_name for part in SENSITIVE_FIELD_PARTS):
        return "[PROTEGIDO]"
    if any(part in lower_name for part in MASKED_FIELD_PARTS):
        return _mask_identifier(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, (Decimal, UUID, date, datetime, Path)):
        return str(value)
    if isinstance(value, FieldFile):
        return Path(value.name).name if value.name else ""
    if isinstance(value, models.Model):
        return {
            "id": str(getattr(value, "uuid", value.pk)),
            "representacao": str(value)[:500],
        }
    if isinstance(value, dict):
        return {
            str(key): normalizar_valor(item, field_name=str(key))
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        return [normalizar_valor(item, field_name=field_name) for item in value]
    text = str(value)
    return text if len(text) <= MAX_TEXT_LENGTH else f"{text[:MAX_TEXT_LENGTH]}…"


def snapshot_model(instance: models.Model | None, *, include_m2m: bool = True) -> dict[str, Any]:
    if instance is None:
        return {}
    snapshot: dict[str, Any] = {}
    for field in instance._meta.concrete_fields:
        name = field.name
        if any(part in name.lower() for part in SENSITIVE_FIELD_PARTS):
            snapshot[name] = "[PROTEGIDO]"
            continue
        try:
            value = getattr(instance, name)
        except Exception:
            continue
        snapshot[name] = normalizar_valor(value, field_name=name)
    if include_m2m and instance.pk:
        for field in instance._meta.many_to_many:
            try:
                related = getattr(instance, field.name).all()
                snapshot[field.name] = [
                    {
                        "id": str(getattr(obj, "uuid", obj.pk)),
                        "representacao": str(obj)[:500],
                    }
                    for obj in related
                ]
            except Exception:
                continue
    return snapshot


def diff_snapshots(
    anteriores: dict[str, Any] | None,
    posteriores: dict[str, Any] | None,
) -> list[str]:
    before = anteriores or {}
    after = posteriores or {}
    return sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))


def _object_metadata(objeto=None, *, recurso: str = "", objeto_id: str = "") -> dict[str, str]:
    if objeto is None:
        return {
            "recurso": recurso[:120],
            "objeto_tipo": recurso[:120],
            "objeto_id": str(objeto_id)[:100],
            "objeto_representacao": "",
        }
    return {
        "recurso": (recurso or objeto._meta.verbose_name)[:120],
        "objeto_tipo": f"{objeto._meta.app_label}.{objeto._meta.model_name}"[:120],
        "objeto_id": str(getattr(objeto, "uuid", objeto.pk))[:100],
        "objeto_representacao": str(objeto)[:500],
    }


def registrar_evento(
    request,
    *,
    tipo: str,
    descricao: str,
    categoria: str = EventoAuditoria.Categoria.ACESSO,
    nivel: str = EventoAuditoria.Nivel.INFORMATIVO,
    ator=None,
    usuario_afetado=None,
    objeto=None,
    recurso: str = "",
    objeto_id: str = "",
    sucesso: bool = True,
    status_http: int | None = None,
    dados_anteriores: dict[str, Any] | None = None,
    dados_posteriores: dict[str, Any] | None = None,
    campos_alterados: list[str] | None = None,
    dados: dict[str, Any] | None = None,
) -> EventoAuditoria:
    metadata = _object_metadata(objeto, recurso=recurso, objeto_id=objeto_id)
    resolved_actor = ator
    if resolved_actor is None:
        resolved_actor = getattr(request, "real_user", None) or getattr(request, "user", None)
    if not getattr(resolved_actor, "is_authenticated", False):
        resolved_actor = None
    if not getattr(usuario_afetado, "is_authenticated", False):
        usuario_afetado = None
    anteriores = normalizar_valor(dados_anteriores or {})
    posteriores = normalizar_valor(dados_posteriores or {})
    changed = campos_alterados
    if changed is None and (anteriores or posteriores):
        changed = diff_snapshots(anteriores, posteriores)
    return EventoAuditoria.objects.create(
        tipo=tipo,
        categoria=categoria,
        nivel=nivel,
        ator=resolved_actor,
        usuario_afetado=usuario_afetado,
        descricao=descricao[:500],
        sucesso=sucesso,
        status_http=status_http,
        metodo_http=getattr(request, "method", "")[:10],
        caminho=getattr(request, "path", "")[:500],
        dados_anteriores=anteriores,
        dados_posteriores=posteriores,
        campos_alterados=changed or [],
        dados=normalizar_valor(dados or {}),
        request_id=getattr(request, "request_id", ""),
        endereco_ip=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        **metadata,
    )


def registrar_mudanca(
    request,
    *,
    tipo: str,
    categoria: str,
    descricao: str,
    objeto,
    anteriores: dict[str, Any] | None,
    posteriores: dict[str, Any] | None,
    usuario_afetado=None,
    dados: dict[str, Any] | None = None,
) -> EventoAuditoria:
    return registrar_evento(
        request,
        tipo=tipo,
        categoria=categoria,
        descricao=descricao,
        objeto=objeto,
        usuario_afetado=usuario_afetado,
        dados_anteriores=anteriores,
        dados_posteriores=posteriores,
        dados=dados,
    )


def pretty_json(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False, indent=2, sort_keys=True)
