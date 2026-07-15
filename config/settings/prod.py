"""
Settings de production.

À compléter avec les secrets via variables d'environnement.
Force DEBUG=False, active les sécurités HTTPS et les cookies sécurisés.
"""
from apps.core.utils import get_env

from .base import *  # noqa: F401,F403
from .base import DATABASES  # noqa: F401

DEBUG = False

ALLOWED_HOSTS = get_env(
    "DJANGO_ALLOWED_HOSTS",
    cast=list,
    default=["localhost"],
)

# Sécurité
SECURE_SSL_REDIRECT = get_env("SECURE_SSL_REDIRECT", cast=bool, default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 jours
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"

# Base de données : PostgreSQL obligatoire en production
DATABASES = {  # noqa: F811
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": get_env("DATABASE_NAME", default="huduma"),
        "USER": get_env("DATABASE_USER", default="huduma"),
        "PASSWORD": get_env("DATABASE_PASSWORD", default=""),
        "HOST": get_env("DATABASE_HOST", default="localhost"),
        "PORT": get_env("DATABASE_PORT", default="5432"),
    }
}

# Fichiers statiques : WhiteNoise recommandé
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Email : SMTP en production
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = get_env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = get_env("EMAIL_PORT", cast=int, default=587)
EMAIL_HOST_USER = get_env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = get_env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = get_env("DEFAULT_FROM_EMAIL", default="Huduma <noreply@huduma.cd>")

EMAIL_BACKEND_PROVIDER = "brevo"
BREVO_API_KEY = get_env("BREVO_API_KEY", default="")
BREVO_SENDER_EMAIL = get_env("BREVO_SENDER_EMAIL", default="noreply@elikya.cd")
BREVO_SENDER_NAME = get_env("BREVO_SENDER_NAME", default="Huduma Kelasi")
