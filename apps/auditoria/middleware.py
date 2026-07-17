from __future__ import annotations

import logging

from .models import EventoAuditoria
from .services import registrar_evento

logger = logging.getLogger(__name__)


class AuditAccessMiddleware:
    """Registra respostas 403 sem interferir na resposta original."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 403 and not getattr(request, "_audit_403_recorded", False):
            try:
                real_user = getattr(request, "real_user", None)
                current_user = getattr(request, "user", None)
                registrar_evento(
                    request,
                    tipo=EventoAuditoria.Tipo.ACESSO_NEGADO,
                    categoria=EventoAuditoria.Categoria.ACESSO,
                    nivel=EventoAuditoria.Nivel.ATENCAO,
                    ator=real_user if getattr(real_user, "is_authenticated", False) else None,
                    usuario_afetado=(
                        current_user
                        if getattr(request, "is_impersonating", False)
                        and getattr(current_user, "is_authenticated", False)
                        else None
                    ),
                    descricao=f"Acesso negado a {request.method} {request.path}.",
                    sucesso=False,
                    status_http=403,
                    dados={
                        "query_string": request.META.get("QUERY_STRING", "")[:1000],
                        "referer": request.META.get("HTTP_REFERER", "")[:500],
                        "impersonacao": bool(getattr(request, "is_impersonating", False)),
                    },
                )
                request._audit_403_recorded = True
            except Exception:
                logger.exception("audit_access_denied_failed")
        return response
