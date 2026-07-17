from pathlib import Path

from django.contrib.messages import constants as message_constants

from .env import get_bool, get_env, get_int, get_list

BASE_DIR = Path(__file__).resolve().parents[2]

SECRET_KEY = get_env("DJANGO_SECRET_KEY", "unsafe-development-key")
DEBUG = get_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = get_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = get_list("DJANGO_CSRF_TRUSTED_ORIGINS")

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

LOCAL_APPS = [
    "apps.core.apps.CoreConfig",
    "apps.contas.apps.ContasConfig",
    "apps.integracoes.apps.IntegracoesConfig",
    "apps.pessoas.apps.PessoasConfig",
    "apps.pontuacao.apps.PontuacaoConfig",
    "apps.comissoes.apps.ComissoesConfig",
    "apps.requerimentos.apps.RequerimentosConfig",
    "apps.triagem.apps.TriagemConfig",
    "apps.cadastros.apps.CadastrosConfig",
    "apps.auditoria.apps.AuditoriaConfig",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.core.middleware.RequestCorrelationMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.contas.middleware.ImpersonationMiddleware",
    "apps.core.middleware.CurrentUserMiddleware",
    "apps.auditoria.middleware.AuditAccessMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.triagem.context_processors.permissoes_triagem",
                "apps.cadastros.context_processors.acesso_cadastros",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": get_env("POSTGRES_DB", "rsc"),
        "USER": get_env("POSTGRES_USER", "rsc"),
        "PASSWORD": get_env("POSTGRES_PASSWORD", ""),
        "HOST": get_env("POSTGRES_HOST", "localhost"),
        "PORT": get_env("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": get_int("POSTGRES_CONN_MAX_AGE", 60),
        "CONN_HEALTH_CHECKS": True,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "contas.Usuario"
LOGIN_URL = "contas:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"
MESSAGE_TAGS = {message_constants.ERROR: "danger"}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = get_env("DJANGO_TIME_ZONE", "America/Bahia")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# MEDIA_ROOT guarda documentos privados. MEDIA_URL existe apenas por exigência
# de compatibilidade do storage; nenhuma rota pública é registrada para esse
# prefixo. Downloads passam por autorização do Django.
MEDIA_URL = "/_private_files_not_public_/"
MEDIA_ROOT = Path(get_env("RSC_MEDIA_ROOT", str(BASE_DIR / "media")))
RSC_USE_X_ACCEL_REDIRECT = get_bool("RSC_USE_X_ACCEL_REDIRECT", False)
RSC_PROTECTED_MEDIA_INTERNAL_URL = get_env(
    "RSC_PROTECTED_MEDIA_INTERNAL_URL", "/_protected_media/"
)

STORAGES = {
    "default": {"BACKEND": "apps.core.storage.PrivateFileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATA_UPLOAD_MAX_MEMORY_SIZE = get_int("RSC_MAX_UPLOAD_BYTES", 52_428_800) + 2_097_152
FILE_UPLOAD_MAX_MEMORY_SIZE = 2_621_440
RSC_MAX_UPLOAD_BYTES = get_int("RSC_MAX_UPLOAD_BYTES", 52_428_800)
RSC_ALLOWED_UPLOAD_EXTENSIONS = get_list("RSC_ALLOWED_UPLOAD_EXTENSIONS")
RSC_ALLOWED_UPLOAD_MIME_TYPES = get_list("RSC_ALLOWED_UPLOAD_MIME_TYPES")

EMAIL_BACKEND = get_env(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = get_env(
    "DEFAULT_FROM_EMAIL", "Sistema RSC <nao-responda@ufsb.edu.br>"
)

REDIS_URL = get_env("REDIS_URL", "redis://localhost:6379/1")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

UFSB_AUTH = {
    "CLIENT_ID": get_env("UFSB_AUTH_CLIENT_ID"),
    "CLIENT_SECRET": get_env("UFSB_AUTH_CLIENT_SECRET"),
    "SCOPE": get_env("UFSB_AUTH_SCOPE", "read"),
    "AUTHORIZATION_URL": get_env("UFSB_AUTHORIZATION_URL"),
    "TOKEN_URL": get_env("UFSB_AUTH_TOKEN_URL"),
    "USERINFO_URL": get_env("UFSB_AUTH_USERINFO_URL"),
    "USERINFO_API_KEY": get_env("UFSB_AUTH_USERINFO_API_KEY"),
    "USER_NAME_ATTRIBUTE": get_env("UFSB_AUTH_USER_NAME_ATTRIBUTE", "pessoa"),
    "LOGOUT_URL": get_env("UFSB_AUTH_LOGOUT_URL"),
    "LOGOUT_SERVICE_URL": get_env("UFSB_AUTH_LOGOUT_SERVICE_URL"),
    "REDIRECT_URI": get_env("UFSB_AUTH_REDIRECT_URI"),
    "TOKEN_AUTH_METHOD": get_env(
        "UFSB_AUTH_TOKEN_AUTH_METHOD", "client_secret_basic"
    ),
    "USE_PKCE": get_bool("UFSB_AUTH_USE_PKCE", False),
    "STATE_TTL_SECONDS": get_int("UFSB_AUTH_STATE_TTL_SECONDS", 600),
    "TIMEOUT_SECONDS": get_int("UFSB_AUTH_TIMEOUT_SECONDS", 10),
    "CONNECT_TIMEOUT_SECONDS": get_int("UFSB_AUTH_CONNECT_TIMEOUT_SECONDS", 3),
    "VERIFY_SSL": get_bool("UFSB_AUTH_VERIFY_SSL", True),
    "CA_BUNDLE": get_env("UFSB_AUTH_CA_BUNDLE"),
}

UFSB_API = {
    "CLIENT_ID": get_env("UFSB_API_CLIENT_ID"),
    "CLIENT_SECRET": get_env("UFSB_API_CLIENT_SECRET"),
    "API_KEY": get_env("UFSB_API_KEY"),
    "TOKEN_URL": get_env("UFSB_API_TOKEN_URL"),
    "SCOPE": get_env("UFSB_API_SCOPE"),
    "TOKEN_AUTH_METHOD": get_env(
        "UFSB_API_TOKEN_AUTH_METHOD", "client_secret_basic"
    ),
    "TIMEOUT_SECONDS": get_int("UFSB_API_TIMEOUT_SECONDS", 10),
    "CONNECT_TIMEOUT_SECONDS": get_int("UFSB_API_CONNECT_TIMEOUT_SECONDS", 3),
    "VERIFY_SSL": get_bool("UFSB_API_VERIFY_SSL", True),
    "CA_BUNDLE": get_env("UFSB_API_CA_BUNDLE"),
    "RATE_LIMIT_ALERT_PERCENT": get_int("UFSB_API_RATE_LIMIT_ALERT_PERCENT", 10),
    "PAGE_PARAM": get_env("UFSB_API_PAGE_PARAM", "page"),
    "QUERY_PARAMS": {
        "USUARIO_ID_USUARIO": get_env(
            "UFSB_API_USUARIOS_ID_USUARIO_PARAM", "id-usuario"
        ),
        "USUARIO_LOGIN": get_env("UFSB_API_USUARIOS_LOGIN_PARAM", "login"),
        "USUARIO_ID_INSTITUCIONAL": get_env(
            "UFSB_API_USUARIOS_ID_INSTITUCIONAL_PARAM", "id-institucional"
        ),
        "SERVIDOR_ID_INSTITUCIONAL": get_env(
            "UFSB_API_SERVIDORES_ID_INSTITUCIONAL_PARAM", "id-institucional"
        ),
    },
    "ENDPOINTS": {
        "USUARIOS": get_env("UFSB_API_USUARIOS_URL"),
        "SERVIDORES": get_env("UFSB_API_SERVIDORES_URL"),
        "UNIDADES": get_env("UFSB_API_UNIDADES_URL"),
        "UNIDADES_LOTACAO": get_env("UFSB_API_UNIDADES_LOTACAO_URL"),
        "UNIDADES_EXERCICIO": get_env("UFSB_API_UNIDADES_EXERCICIO_URL"),
        "LOCALIZACOES_SERVIDORES": get_env("UFSB_API_LOCALIZACOES_SERVIDORES_URL"),
        "RESPONSAVEIS": get_env("UFSB_API_RESPONSAVEIS_URL"),
        "ARQUIVOS": get_env("UFSB_API_ARQUIVOS_URL"),
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_context": {"()": "apps.core.logging.RequestContextFilter"},
    },
    "formatters": {
        "json": {"()": "apps.core.logging.JsonFormatter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["request_context"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": get_env("DJANGO_LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
