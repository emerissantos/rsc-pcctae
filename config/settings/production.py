from .base import *  # noqa: F403
from .env import get_bool

DEBUG = False

if SECRET_KEY == "unsafe-development-key":  # noqa: F405
    raise RuntimeError("DJANGO_SECRET_KEY deve ser definida em produção.")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = get_bool("DJANGO_USE_X_FORWARDED_HOST", False)
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_SSL_REDIRECT = get_bool("DJANGO_SECURE_SSL_REDIRECT", True)
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

# O Nginx entrega o arquivo somente após autorização da view Django.
RSC_USE_X_ACCEL_REDIRECT = get_bool("RSC_USE_X_ACCEL_REDIRECT", True)
