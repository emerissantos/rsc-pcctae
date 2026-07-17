from __future__ import annotations

import logging

from django.http import HttpResponseForbidden
from django.urls import reverse

from apps.auditoria.models import EventoAuditoria, SessaoImpersonacao
from apps.auditoria.services import registrar_evento

from .permissions import pode_simular_usuario

logger = logging.getLogger(__name__)

IMPERSONATION_SESSION_KEY = "rsc_impersonation_uuid"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class ImpersonationMiddleware:
    """Substitui request.user pelo alvo, mantendo o ator autenticado na sessão Django."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.real_user = getattr(request, "user", None)
        request.is_impersonating = False
        request.impersonation_session = None

        session_uuid = request.session.get(IMPERSONATION_SESSION_KEY)
        actor = request.real_user
        if not session_uuid or not actor or not actor.is_authenticated:
            return self.get_response(request)

        sessao = (
            SessaoImpersonacao.objects.select_related("ator", "usuario_simulado")
            .filter(uuid=session_uuid, encerrada_em__isnull=True)
            .first()
        )
        if not sessao:
            request.session.pop(IMPERSONATION_SESSION_KEY, None)
            request.session.modified = True
            return self.get_response(request)

        if sessao.ator_id != actor.pk or not pode_simular_usuario(actor):
            sessao.encerrar(usuario=actor, motivo="Sessão inválida ou permissão removida.")
            registrar_evento(
                request,
                tipo=EventoAuditoria.Tipo.IMPERSONACAO_ENCERRADA,
                categoria=EventoAuditoria.Categoria.IMPERSONACAO,
                nivel=EventoAuditoria.Nivel.ATENCAO,
                ator=actor,
                usuario_afetado=sessao.usuario_simulado,
                objeto=sessao,
                descricao=(
                    "Simulação encerrada porque a sessão ficou inválida "
                    "ou a permissão foi removida."
                ),
                dados={"motivo_encerramento": sessao.motivo_encerramento},
            )
            request.session.pop(IMPERSONATION_SESSION_KEY, None)
            request.session.modified = True
            return self.get_response(request)

        target = sessao.usuario_simulado
        if not target.is_active or target.is_superuser:
            sessao.encerrar(usuario=actor, motivo="Usuário simulado indisponível.")
            registrar_evento(
                request,
                tipo=EventoAuditoria.Tipo.IMPERSONACAO_ENCERRADA,
                categoria=EventoAuditoria.Categoria.IMPERSONACAO,
                nivel=EventoAuditoria.Nivel.ATENCAO,
                ator=actor,
                usuario_afetado=sessao.usuario_simulado,
                objeto=sessao,
                descricao="Simulação encerrada porque o usuário simulado ficou indisponível.",
                dados={"motivo_encerramento": sessao.motivo_encerramento},
            )
            request.session.pop(IMPERSONATION_SESSION_KEY, None)
            request.session.modified = True
            return self.get_response(request)

        request.user = target
        request.is_impersonating = True
        request.impersonation_session = sessao

        stop_path = reverse("contas:impersonar-encerrar")
        if request.method not in SAFE_METHODS and request.path != stop_path:
            registrar_evento(
                request,
                tipo=EventoAuditoria.Tipo.ACAO_BLOQUEADA_IMPERSONACAO,
                categoria=EventoAuditoria.Categoria.IMPERSONACAO,
                nivel=EventoAuditoria.Nivel.ATENCAO,
                ator=actor,
                usuario_afetado=target,
                descricao="Ação de escrita bloqueada durante simulação de usuário.",
                sucesso=False,
                status_http=403,
                dados={"metodo": request.method, "caminho": request.path[:500]},
            )
            logger.warning(
                "impersonation_write_blocked",
                extra={
                    "actor_id": actor.pk,
                    "target_id": target.pk,
                    "path": request.path,
                    "method": request.method,
                },
            )
            return HttpResponseForbidden(
                "A simulação de usuário funciona em modo somente leitura. "
                "Encerre a simulação para realizar alterações."
            )

        return self.get_response(request)
