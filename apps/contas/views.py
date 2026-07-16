from __future__ import annotations

import logging
import secrets
import time
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.auditoria.models import SessaoImpersonacao
from apps.auditoria.services import get_client_ip
from apps.integracoes.common.exceptions import IntegrationError
from apps.integracoes.ufsb.oauth.client import UFSBOAuthClient
from apps.integracoes.ufsb.oauth.services import AuthenticateUFSBUserService

from .forms import JustificativaImpersonacaoForm
from .middleware import IMPERSONATION_SESSION_KEY
from .models import Usuario
from .permissions import pode_simular_usuario, usuario_pode_ser_simulado
from .services import ProvisionarUsuarioUFSBService

logger = logging.getLogger(__name__)

OAUTH_SESSION_KEY = "ufsb_oauth_flow"


@never_cache
@require_GET
def login(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    configured = all(
        [
            settings.UFSB_AUTH.get("CLIENT_ID"),
            settings.UFSB_AUTH.get("CLIENT_SECRET"),
            settings.UFSB_AUTH.get("AUTHORIZATION_URL"),
            settings.UFSB_AUTH.get("TOKEN_URL"),
            settings.UFSB_AUTH.get("USERINFO_URL"),
            settings.UFSB_AUTH.get("REDIRECT_URI"),
        ]
    )
    return render(request, "contas/login.html", {"oauth_configured": configured})


@never_cache
@require_GET
def oauth_start(request):
    client = UFSBOAuthClient()
    try:
        state = client.generate_state()
        code_verifier = client.generate_pkce_verifier() if settings.UFSB_AUTH["USE_PKCE"] else None
        next_url = request.GET.get("next", settings.LOGIN_REDIRECT_URL)
        if not url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            next_url = settings.LOGIN_REDIRECT_URL
        request.session[OAUTH_SESSION_KEY] = {
            "state": state,
            "created_at": int(time.time()),
            "next": next_url,
            "code_verifier": code_verifier,
        }
        request.session.modified = True
        return redirect(client.build_authorization_url(state=state, code_verifier=code_verifier))
    except IntegrationError:
        logger.exception("oauth_start_failed")
        messages.error(request, "A autenticação institucional não está disponível neste momento.")
        return redirect("contas:login")


@never_cache
@require_GET
def oauth_callback(request):
    flow = request.session.pop(OAUTH_SESSION_KEY, None)
    request.session.modified = True
    if not isinstance(flow, dict):
        messages.error(
            request,
            "A tentativa de autenticação expirou ou não foi iniciada neste navegador.",
        )
        return redirect("contas:login")

    returned_state = request.GET.get("state", "")
    expected_state = str(flow.get("state") or "")
    age = int(time.time()) - int(flow.get("created_at") or 0)
    if (
        not returned_state
        or not expected_state
        or not secrets.compare_digest(returned_state, expected_state)
        or age < 0
        or age > settings.UFSB_AUTH["STATE_TTL_SECONDS"]
    ):
        messages.error(
            request,
            "A validação de segurança da autenticação falhou. "
            "Inicie o acesso novamente.",
        )
        return redirect("contas:login")

    provider_error = request.GET.get("error")
    if provider_error:
        logger.warning("oauth_provider_error", extra={"provider_error": provider_error})
        messages.warning(request, "A autenticação institucional foi cancelada ou recusada.")
        return redirect("contas:login")

    code = request.GET.get("code")
    if not code:
        messages.error(request, "O provedor não retornou o código de autorização esperado.")
        return redirect("contas:login")

    try:
        userinfo = AuthenticateUFSBUserService().execute(
            code=code,
            code_verifier=flow.get("code_verifier"),
        )
        result = ProvisionarUsuarioUFSBService().execute(
            userinfo=userinfo,
            correlation_id=getattr(request, "correlation_id", ""),
        )
        django_login(
            request,
            result.usuario,
            backend="django.contrib.auth.backends.ModelBackend",
        )
        messages.success(request, "Autenticação realizada com sucesso.")
        if result.vinculos_count == 0:
            messages.info(
                request,
                "A conta foi identificada, mas nenhum vínculo funcional foi localizado.",
            )
        return redirect(flow.get("next") or settings.LOGIN_REDIRECT_URL)
    except IntegrationError as exc:
        logger.exception(
            "oauth_callback_failed",
            extra={"status_code": getattr(exc, "status_code", None)},
        )
        messages.error(request, str(exc))
        return redirect("contas:login")


@never_cache
@require_POST
def logout(request):
    django_logout(request)
    logout_url = settings.UFSB_AUTH.get("LOGOUT_URL")
    if logout_url:
        service_url = settings.UFSB_AUTH.get("LOGOUT_SERVICE_URL") or request.build_absolute_uri(
            reverse("core:home")
        )
        separator = "&" if "?" in logout_url else "?"
        return redirect(f"{logout_url}{separator}{urlencode({'service': service_url})}")
    messages.success(request, "Sessão encerrada.")
    return redirect("core:home")


@never_cache
@require_http_methods(["GET", "POST"])
def impersonar_iniciar(request, usuario_uuid):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('contas:login')}?next={request.path}")
    ator = getattr(request, "real_user", request.user)
    if getattr(request, "is_impersonating", False) or not pode_simular_usuario(ator):
        raise PermissionDenied
    alvo = get_object_or_404(Usuario, uuid=usuario_uuid)
    if not usuario_pode_ser_simulado(ator, alvo):
        raise PermissionDenied

    form = JustificativaImpersonacaoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        for sessao_anterior in SessaoImpersonacao.objects.filter(
            ator=ator,
            encerrada_em__isnull=True,
        ):
            sessao_anterior.encerrar(
                usuario=ator,
                motivo="Encerrada automaticamente ao iniciar nova simulação.",
            )
        request.session.cycle_key()
        sessao = SessaoImpersonacao.objects.create(
            ator=ator,
            usuario_simulado=alvo,
            justificativa=form.cleaned_data["justificativa"],
            iniciada_em=timezone.now(),
            request_id_inicio=getattr(request, "request_id", ""),
            endereco_ip_inicio=get_client_ip(request),
            user_agent_inicio=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        request.session[IMPERSONATION_SESSION_KEY] = str(sessao.uuid)
        request.session.modified = True
        messages.warning(
            request,
            f"Simulação iniciada como {alvo}. O modo é somente leitura.",
        )
        return redirect("core:home")

    return render(
        request,
        "contas/impersonar_confirmar.html",
        {"form": form, "alvo": alvo},
    )


@never_cache
@require_POST
def impersonar_encerrar(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    ator = getattr(request, "real_user", request.user)
    sessao = getattr(request, "impersonation_session", None)
    if not getattr(request, "is_impersonating", False) or not sessao:
        raise PermissionDenied
    sessao.encerrar(usuario=ator, motivo="Encerrada manualmente pelo usuário técnico.")
    request.session.pop(IMPERSONATION_SESSION_KEY, None)
    request.session.cycle_key()
    request.session.modified = True
    messages.success(request, f"Simulação de {sessao.usuario_simulado} encerrada.")
    return redirect("cadastros:lista", resource_slug="usuarios")
