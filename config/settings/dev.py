"""
Settings de développement.

Utilise SQLite par défaut pour démarrage rapide. Pour utiliser
PostgreSQL, positionner DATABASE_ENGINE=postgres dans .env.
"""
from apps.core.utils import get_env

from .base import *  # noqa: F401,F403
from .base import BASE_DIR, DATABASES, INSTALLED_APPS, MIDDLEWARE  # noqa: F401

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Base de données
_db_engine = get_env("DATABASE_ENGINE", default="sqlite")

if _db_engine == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": get_env("DATABASE_NAME", default="huduma"),
            "USER": get_env("DATABASE_USER", default="huduma"),
            "PASSWORD": get_env("DATABASE_PASSWORD", default="huduma"),
            "HOST": get_env("DATABASE_HOST", default="localhost"),
            "PORT": get_env("DATABASE_PORT", default="5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

try:
    import debug_toolbar  # noqa: F401

    INSTALLED_APPS = list(INSTALLED_APPS) + ["debug_toolbar"]
    MIDDLEWARE = list(MIDDLEWARE) + ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    INTERNAL_IPS = ["127.0.0.1", "0.0.0.0"]
except ImportError:
    pass

# Email : console en dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "huduma-dev@localhost"
