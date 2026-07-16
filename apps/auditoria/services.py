from __future__ import annotations

from ipaddress import ip_address
from typing import Any

from .models import EventoAuditoria


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


def registrar_evento(
    request,
    *,
    tipo: str,
    descricao: str,
    ator=None,
    usuario_afetado=None,
    dados: dict[str, Any] | None = None,
) -> EventoAuditoria:
    return EventoAuditoria.objects.create(
        tipo=tipo,
        ator=ator or getattr(request, "real_user", None) or getattr(request, "user", None),
        usuario_afetado=usuario_afetado,
        descricao=descricao[:500],
        dados=dados or {},
        request_id=getattr(request, "request_id", ""),
        endereco_ip=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
    )
