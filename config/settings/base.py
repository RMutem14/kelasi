"""
Settings de base partagés par tous les environnements.

Ne jamais mettre de secrets ici. Utiliser des variables d'environnement
via ``.env`` (chargé par python-dotenv).
"""
from pathlib import Path

from django.utils.translation import gettext_lazy as _

from dotenv import load_dotenv

from apps.core.utils import get_env

load_dotenv()

# Chemin racine du projet : config/settings/base.py -> ../../ = dossier projet
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Sécurité
SECRET_KEY = get_env("SECRET_KEY", default="dev-insecure-key-change-me")
DEBUG = get_env("DEBUG", cast=bool, default=False)
ALLOWED_HOSTS = get_env("DJANGO_ALLOWED_HOSTS", cast=list, default=["localhost", "127.0.0.1"])

# Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Apps métier
    "apps.core",
    "apps.accounts",
    "apps.dashboard",
    "apps.academic",
    "apps.pedagogy",
    "apps.validation",
    "apps.marketplace",
    "apps.students",
    "apps.parents",
    "apps.finance",
    "apps.attendance",
    "apps.schedule",
    "apps.forum",
    "apps.notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Templates
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
                "apps.core.context_processors.app_globals",
            ],
        },
    },
]

# Base de données (surchargé par dev.py / prod.py)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Authentification
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# URLs d'authentification (noms d'URL inversés)
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"


# Internationalisation
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Kinshasa"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("fr", _("Français")),
    ("ln", _("Lingala")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

LANGUAGE_COOKIE_NAME = "huduma_language"
LANGUAGE_COOKIE_AGE = 31536000  # 1 an


# Fichiers statiques et médias
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Stockage par défaut pour les fichiers uploadés
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Pagination par défaut des listes
PAGINATION_DEFAULT_PAGE_SIZE = 25

# Passerelle de paiement (simulated | orange_money | mpesa | ikeepay)
MARKETPLACE_PAYMENT_GATEWAY = "simulated"

# Fournisseur email (console | brevo)
EMAIL_BACKEND_PROVIDER = "console"

# Cache (fallback local memory for dev/test)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "huduma-default",
        "TIMEOUT": 300,  # 5 minutes par défaut
    }
}

# Session cache pour performances
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Headers de cache pour static files
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Logging — configuration par défaut (console)
# Surchargée dans prod.py pour écrire dans des fichiers.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
