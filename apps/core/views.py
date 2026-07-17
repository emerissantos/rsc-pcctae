from pathlib import Path

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from apps.auditoria.models import EventoAuditoria
from apps.auditoria.services import registrar_evento

from .profile import carregar_dados_funcionais


@require_GET
def home(request):
    if not request.user.is_authenticated:
        return redirect("contas:login")
    contexto = {}
    if request.user.is_authenticated:
        from apps.pontuacao.models import ItemPontuacao
        from apps.requerimentos.models import Requerimento

        queryset = Requerimento.objects.filter(requerente=request.user).select_related(
            "nivel_pretendido", "vinculo"
        )
        finalizados = queryset.filter(
            situacao__in=[Requerimento.Situacao.DEFERIDO, Requerimento.Situacao.INDEFERIDO]
        ).count()
        contexto = {
            "resumo": {
                "total": queryset.count(),
                "ativos": queryset.exclude(
                    situacao__in=[
                        Requerimento.Situacao.DEFERIDO,
                        Requerimento.Situacao.INDEFERIDO,
                        Requerimento.Situacao.CANCELADO,
                    ]
                ).count(),
                "finalizados": finalizados,
                "itens": ItemPontuacao.objects.filter(ativo=True).count(),
            },
            "recentes": queryset[:5],
        }
    return render(request, "core/home.html", contexto)


@require_GET
def meus_dados(request):
    if not request.user.is_authenticated:
        return redirect("contas:login")

    dados_funcionais = carregar_dados_funcionais(request.user)
    objeto_auditoria = (
        dados_funcionais.servidor
        or dados_funcionais.pessoa
        or dados_funcionais.identidade
        or request.user
    )
    registrar_evento(
        request,
        tipo=EventoAuditoria.Tipo.DADOS_FUNCIONAIS_VISUALIZADOS,
        categoria=EventoAuditoria.Categoria.ACESSO,
        descricao=f"Dados funcionais consultados por {request.user}",
        usuario_afetado=request.user,
        objeto=objeto_auditoria,
        dados={
            "possui_identidade_externa": dados_funcionais.identidade is not None,
            "possui_pessoa_institucional": dados_funcionais.pessoa is not None,
            "possui_servidor": dados_funcionais.servidor is not None,
            "quantidade_vinculos": len(dados_funcionais.vinculos),
            "quantidade_vinculos_ativos": sum(
                1 for vinculo in dados_funcionais.vinculos if vinculo.ativo
            ),
        },
    )
    identidade = dados_funcionais.identidade
    pessoa = dados_funcionais.pessoa
    servidor = dados_funcionais.servidor
    apresentacao = {
        "nome_principal": (
            getattr(servidor, "nome_atual", "")
            or getattr(pessoa, "nome", "")
            or getattr(identidade, "nome_recebido", "")
            or request.user.nome_exibicao
            or request.user.username
        ),
        "email_principal": (
            getattr(servidor, "email_atual", "")
            or getattr(pessoa, "email_institucional", "")
            or getattr(identidade, "email_recebido", "")
            or request.user.email
            or "E-mail institucional não informado"
        ),
        "nome_institucional": (
            getattr(pessoa, "nome", "")
            or getattr(identidade, "nome_recebido", "")
            or request.user.nome_exibicao
            or request.user.username
        ),
        "nome_identificacao": getattr(pessoa, "nome_identificacao", "") or "Não informado",
        "login": getattr(identidade, "login", "") or request.user.username,
        "email_institucional": (
            getattr(pessoa, "email_institucional", "")
            or getattr(identidade, "email_recebido", "")
            or request.user.email
            or "Não informado"
        ),
        "id_institucional": (
            getattr(pessoa, "id_institucional", None)
            or getattr(identidade, "id_institucional", None)
            or "Não informado"
        ),
        "ultima_sincronizacao": (
            getattr(identidade, "ultima_sincronizacao_em", None)
            or getattr(pessoa, "sincronizado_em", None)
        ),
    }
    return render(
        request,
        "core/meus_dados.html",
        {
            "dados_funcionais": dados_funcionais,
            "apresentacao": apresentacao,
        },
    )


@never_cache
@require_GET
def health_live(request):
    return JsonResponse({"status": "ok", "service": "rsc-pcctae"})


@never_cache
@require_GET
def health_ready(request):
    checks: dict[str, str] = {}
    status_code = 200
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
        status_code = 503
    try:
        media_root = Path(settings.MEDIA_ROOT)
        media_root.mkdir(parents=True, exist_ok=True)
        checks["media"] = "ok" if media_root.is_dir() else "error"
    except OSError:
        checks["media"] = "error"
        status_code = 503
    return JsonResponse(
        {"status": "ok" if status_code == 200 else "degraded", "checks": checks},
        status=status_code,
    )


def error_403(request, exception=None):
    return render(request, "errors/403.html", status=403)


def error_404(request, exception=None):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)
