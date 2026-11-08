"""
Configuration Django de MentorMe.

Toute la configuration sensible vient de variables d'environnement
(voir .env.example). Par défaut, le mode est PRODUCTION (DJANGO_DEBUG=0) :
le projet refuse de démarrer sans SECRET_KEY, ALLOWED_HOSTS, DATABASE_URL
et REDIS_URL.
"""
import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

try:  # .env optionnel en développement
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env", override=True)
except ImportError:  # pragma: no cover
    pass


# --------------------------------------------------------------------------
# Helpers d'environnement
# --------------------------------------------------------------------------
def env(name, default=None):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [
        item.strip()
        for item in os.environ.get(name, default).split(",")
        if item.strip()
    ]


# --------------------------------------------------------------------------
# Base
# --------------------------------------------------------------------------
DEBUG = env_bool("DJANGO_DEBUG", False)

SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"
    else:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY est obligatoire.")

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1,10.0.2.2,testserver" if DEBUG else "",
)
if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS est obligatoire.")

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")


# --------------------------------------------------------------------------
# Applications
# --------------------------------------------------------------------------
INSTALLED_APPS = [
    "daphne",  # serveur ASGI : runserver gère aussi les WebSockets

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "channels",

    "accounts",
    "profiles",
    "projects",
    "posts",
    "mentors",
    "booking",
    "audit_ai",
    "messaging",
    "follows",
    "reviews",
    "notifications",
    "matching",
    "calls",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

AUTH_USER_MODEL = "accounts.CustomUser"


# --------------------------------------------------------------------------
# Base de données (PostgreSQL en production)
# --------------------------------------------------------------------------
def database_from_env():
    url = (env("DATABASE_URL") or "").strip().strip('"').strip("'")
    if "://" not in url:
        url = ""

    if not url:
        if DEBUG:
            return {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        raise ImproperlyConfigured(
            "DATABASE_URL est obligatoire hors DEBUG "
            "(ex. postgres://user:pass@host:5432/mentorme)."
        )

    parsed = urlparse(url)

    if parsed.scheme in {"postgres", "postgresql"}:
        config = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/"),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "localhost",
            "PORT": parsed.port or 5432,
            "CONN_MAX_AGE": int(env("DB_CONN_MAX_AGE", "60")),
        }
        options = dict(parse_qsl(parsed.query))  # ex. sslmode=require
        if options:
            config["OPTIONS"] = options
        return config

    if parsed.scheme == "sqlite":
        # sqlite:///relatif.db  ou  sqlite:////chemin/absolu.db
        path = parsed.path
        if path.startswith("//"):
            name = path[1:]
        else:
            name = path.lstrip("/")
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": name or BASE_DIR / "db.sqlite3",
        }

    raise ImproperlyConfigured(f"Schéma DATABASE_URL non géré : {parsed.scheme}")


DATABASES = {"default": database_from_env()}


# --------------------------------------------------------------------------
# Redis : cache (throttling) + couche Channels (WebSocket)
# --------------------------------------------------------------------------
REDIS_URL = (env("REDIS_URL") or "").strip().strip('"').strip("'")
if "://" not in REDIS_URL:
    REDIS_URL = ""

if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        }
    }
elif DEBUG:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
    CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }
else:
    raise ImproperlyConfigured("REDIS_URL est obligatoire hors DEBUG.")


# --------------------------------------------------------------------------
# Django REST Framework / JWT
# --------------------------------------------------------------------------
_renderers = ["rest_framework.renderers.JSONRenderer"]
if DEBUG:
    _renderers.append("rest_framework.renderers.BrowsableAPIRenderer")

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_RENDERER_CLASSES": _renderers,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("THROTTLE_ANON", "60/min"),
        "user": env("THROTTLE_USER", "300/min"),
        "auth": env("THROTTLE_AUTH", "10/min"),        # login, inscription
        "ai_audit": env("THROTTLE_AI_AUDIT", "5/hour"),  # coût IA
        "password_reset": env("THROTTLE_PASSWORD_RESET", "5/hour"),
        "support": env("THROTTLE_SUPPORT", "5/hour"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}


# --------------------------------------------------------------------------
# CORS (nécessaire pour Flutter Web ; inutile pour les apps mobiles)
# --------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = False


# --------------------------------------------------------------------------
# Mots de passe
# --------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --------------------------------------------------------------------------
# Internationalisation
# --------------------------------------------------------------------------
LANGUAGE_CODE = "fr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# --------------------------------------------------------------------------
# Fichiers statiques et médias
# --------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = Path(env("MEDIA_ROOT", str(BASE_DIR / "media")))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --------------------------------------------------------------------------
# Sécurité HTTP (actif hors DEBUG)
# --------------------------------------------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

if not DEBUG:
    # À désactiver (=0) uniquement si le TLS est terminé par un proxy qui
    # redirige déjà en HTTPS.
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(env("DJANGO_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    if env_bool("DJANGO_BEHIND_PROXY", True):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# --------------------------------------------------------------------------
# E-mail (réinitialisation du mot de passe)
# --------------------------------------------------------------------------
# Sans EMAIL_HOST, les e-mails s'affichent dans le terminal du serveur
# (pratique en développement ; en production il faut un vrai service SMTP).
EMAIL_HOST = env("EMAIL_HOST", "")
if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_PORT = int(env("EMAIL_PORT", "587"))
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "MentorMe <no-reply@mentorme.app>")


# --------------------------------------------------------------------------
# IA
# --------------------------------------------------------------------------
# "mock" (développement) ou "openai"
AUDIT_PROVIDER = env("AUDIT_PROVIDER", "mock")
OPENAI_API_KEY = env("OPENAI_API_KEY", "")
OPENAI_MODEL = env("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT_SECONDS = int(env("OPENAI_TIMEOUT_SECONDS", "60"))

if AUDIT_PROVIDER == "openai" and not OPENAI_API_KEY:
    raise ImproperlyConfigured(
        "OPENAI_API_KEY est obligatoire quand AUDIT_PROVIDER=openai."
    )


# --------------------------------------------------------------------------
# Logs
# --------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
    },
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}
