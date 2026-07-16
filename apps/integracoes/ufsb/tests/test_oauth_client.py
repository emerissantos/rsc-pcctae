from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse

from django.test import SimpleTestCase, override_settings

from apps.integracoes.ufsb.oauth.client import UFSBOAuthClient

AUTH_CONFIG = {
    "CLIENT_ID": "rsc-client",
    "CLIENT_SECRET": "secret",
    "SCOPE": "read",
    "AUTHORIZATION_URL": "https://auth.example/authorize",
    "TOKEN_URL": "https://auth.example/token",
    "USERINFO_URL": "https://api.example/me",
    "USERINFO_API_KEY": "",
    "USER_NAME_ATTRIBUTE": "pessoa",
    "REDIRECT_URI": "https://rsc.example/callback/",
    "TOKEN_AUTH_METHOD": "client_secret_basic",
    "USE_PKCE": False,
    "STATE_TTL_SECONDS": 600,
    "TIMEOUT_SECONDS": 10,
    "CONNECT_TIMEOUT_SECONDS": 3,
    "VERIFY_SSL": True,
    "CA_BUNDLE": "",
    "LOGOUT_URL": "",
    "LOGOUT_SERVICE_URL": "",
}


@override_settings(UFSB_AUTH=AUTH_CONFIG)
class OAuthClientTests(SimpleTestCase):
    def test_monta_url_de_autorizacao_com_state(self):
        url = UFSBOAuthClient().build_authorization_url(state="state-seguro")
        query = parse_qs(urlparse(url).query)
        self.assertEqual(query["client_id"], ["rsc-client"])
        self.assertEqual(query["state"], ["state-seguro"])
        self.assertEqual(query["response_type"], ["code"])

    def test_normaliza_userinfo_aninhado_em_pessoa(self):
        info = UFSBOAuthClient().normalize_user_info(
            {
                "pessoa": {
                    "id-usuario": 10,
                    "id-institucional": 20,
                    "login": "fulano",
                    "nome-pessoa": "FULANO",
                    "email": "fulano@ufsb.edu.br",
                }
            }
        )
        self.assertEqual(info.id_usuario, 10)
        self.assertEqual(info.id_institucional, 20)
        self.assertEqual(info.login, "fulano")

    def test_normaliza_pessoa_numerica_como_id_institucional(self):
        info = UFSBOAuthClient().normalize_user_info({"pessoa": 201500028508})
        self.assertEqual(info.id_institucional, 201500028508)
        self.assertIsNone(info.login)

    def test_troca_codigo_sem_persistir_token(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "access_token": "token-temporario",
            "token_type": "Bearer",
            "expires_in": 300,
        }
        session = Mock()
        session.post.return_value = response
        token = UFSBOAuthClient(session=session).exchange_code(code="codigo")
        self.assertEqual(token.access_token, "token-temporario")
        kwargs = session.post.call_args.kwargs
        self.assertNotIn("client_secret", kwargs["data"])
        self.assertEqual(kwargs["auth"], ("rsc-client", "secret"))
