import time
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.contas.models import Usuario
from apps.integracoes.ufsb.oauth.schemas import OAuthUserInfo

AUTH_CONFIG = {
    "CLIENT_ID": "client",
    "CLIENT_SECRET": "secret",
    "SCOPE": "read",
    "AUTHORIZATION_URL": "https://auth.example/authorize",
    "TOKEN_URL": "https://auth.example/token",
    "USERINFO_URL": "https://api.example/me",
    "USERINFO_API_KEY": "",
    "USER_NAME_ATTRIBUTE": "pessoa",
    "LOGOUT_URL": "",
    "LOGOUT_SERVICE_URL": "",
    "REDIRECT_URI": "http://testserver/autenticacao/callback/",
    "TOKEN_AUTH_METHOD": "client_secret_basic",
    "USE_PKCE": False,
    "STATE_TTL_SECONDS": 600,
    "TIMEOUT_SECONDS": 10,
    "CONNECT_TIMEOUT_SECONDS": 3,
    "VERIFY_SSL": True,
    "CA_BUNDLE": "",
}


@override_settings(UFSB_AUTH=AUTH_CONFIG)
class OAuthViewTests(TestCase):
    def test_callback_rejeita_state_invalido(self):
        session = self.client.session
        session["ufsb_oauth_flow"] = {
            "state": "esperado",
            "created_at": int(time.time()),
            "next": "/",
            "code_verifier": None,
        }
        session.save()
        response = self.client.get(
            reverse("contas:oauth-callback"),
            {"state": "outro", "code": "codigo"},
        )
        self.assertRedirects(response, reverse("contas:login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    @patch("apps.contas.views.ProvisionarUsuarioUFSBService")
    @patch("apps.contas.views.AuthenticateUFSBUserService")
    def test_callback_autentica_sem_guardar_token_na_sessao(self, auth_cls, provision_cls):
        user = Usuario.objects.create(username="fulano", is_active=True)
        user.set_unusable_password()
        user.save()
        auth_cls.return_value.execute.return_value = OAuthUserInfo(
            id_usuario=10,
            id_institucional=20,
            login="fulano",
            nome="FULANO",
            email="fulano@ufsb.edu.br",
            raw={},
        )
        provision_cls.return_value.execute.return_value = Mock(usuario=user, vinculos_count=1)
        session = self.client.session
        session["ufsb_oauth_flow"] = {
            "state": "seguro",
            "created_at": int(time.time()),
            "next": "/",
            "code_verifier": None,
        }
        session.save()
        response = self.client.get(
            reverse("contas:oauth-callback"),
            {"state": "seguro", "code": "codigo"},
        )
        self.assertRedirects(response, "/")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.assertNotIn("access_token", self.client.session)
