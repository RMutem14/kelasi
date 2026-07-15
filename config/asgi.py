"""
ASGI config for the Huduma project.

Surcharge ``DJANGO_SETTINGS_MODULE`` par défaut sur ``config.settings.dev``.
En production, positionner la variable d'environnement explicitement.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_asgi_application()
