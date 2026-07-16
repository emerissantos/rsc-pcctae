from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Em desenvolvimento, cookies permanecem compatíveis com HTTP local.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
