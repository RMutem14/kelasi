from django.apps import AppConfig


class MarketplaceConfig(AppConfig):
    name = 'apps.marketplace'
    verbose_name = "Marketplace — Ressources & Portefeuilles"

    def ready(self):
        """Connecte les signaux (crédit wallet automatique sur vente)."""
        from apps.marketplace import signals  # noqa: F401
