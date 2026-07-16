from pathlib import Path

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


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
