from unittest.mock import Mock

from django.test import SimpleTestCase, override_settings

from apps.integracoes.ufsb.api.client import UFSBApiClient

API_CONFIG = {
    "CLIENT_ID": "api-client",
    "CLIENT_SECRET": "secret",
    "API_KEY": "api-key-segura",
    "TOKEN_URL": "https://auth.example/token",
    "SCOPE": "",
    "TOKEN_AUTH_METHOD": "client_secret_basic",
    "TIMEOUT_SECONDS": 10,
    "CONNECT_TIMEOUT_SECONDS": 3,
    "VERIFY_SSL": True,
    "CA_BUNDLE": "",
    "RATE_LIMIT_ALERT_PERCENT": 10,
    "PAGE_PARAM": "page",
    "QUERY_PARAMS": {},
    "ENDPOINTS": {},
}


@override_settings(UFSB_API=API_CONFIG)
class APIClientTests(SimpleTestCase):
    def test_envio_do_bearer_e_x_api_key(self):
        response = Mock(status_code=200)
        response.json.return_value = [{"id": 1}]
        response.headers = {
            "X-Pages": "2",
            "X-Total": "10",
            "X-RateLimit-Limit-Hour": "20000",
            "X-RateLimit-Remaining-Hour": "19525",
            "RateLimit-Reset": "1022",
        }
        session = Mock()
        session.request.return_value = response
        token_service = Mock()
        token_service.get_access_token.return_value = "token-tecnico"

        result = UFSBApiClient(session=session, token_service=token_service).get(
            "https://api.example/usuarios"
        )
        headers = session.request.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer token-tecnico")
        self.assertEqual(headers["x-api-key"], "api-key-segura")
        self.assertEqual(result.page.pages, 2)
        self.assertEqual(result.page.total, 10)
        self.assertEqual(result.rate_limit.remaining, 19525)

    def test_renova_token_uma_vez_apos_401(self):
        unauthorized = Mock(status_code=401, headers={})
        success = Mock(status_code=200, headers={})
        success.json.return_value = []
        session = Mock()
        session.request.side_effect = [unauthorized, success]
        token_service = Mock()
        token_service.get_access_token.side_effect = ["token-antigo", "token-novo"]

        result = UFSBApiClient(session=session, token_service=token_service).get(
            "https://api.example/usuarios"
        )

        self.assertEqual(result.status_code, 200)
        token_service.invalidate.assert_called_once_with()
        self.assertEqual(session.request.call_count, 2)
        second_headers = session.request.call_args_list[1].kwargs["headers"]
        self.assertEqual(second_headers["Authorization"], "Bearer token-novo")
