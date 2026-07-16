from django.test import SimpleTestCase

from apps.core.logging import sanitize_text


class LoggingSanitizationTests(SimpleTestCase):
    def test_remove_codigo_oauth_e_bearer(self):
        text = (
            'GET /autenticacao/callback/?code=codigo-secreto&state=estado HTTP/1.1 '
            'Authorization: Bearer token.secreto'
        )
        sanitized = sanitize_text(text)
        self.assertNotIn("codigo-secreto", sanitized)
        self.assertNotIn("estado HTTP", sanitized)
        self.assertNotIn("token.secreto", sanitized)
        self.assertIn("code=***", sanitized)
        self.assertIn("Bearer ***", sanitized)
