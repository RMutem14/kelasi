"""Configuration de l'application core."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration de l'application core."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core — Fondations techniques"

    def ready(self):
        """Connecte les signaux quand l'app est prête."""
        # Importer les signaux pour les connecter
        from apps.core import signals  # noqa: F401
