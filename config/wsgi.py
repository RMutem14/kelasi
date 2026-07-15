"""
WSGI config for the Huduma project.

Surcharge ``DJANGO_SETTINGS_MODULE`` par défaut sur ``config.settings.dev``.
En production, positionner la variable d'environnement explicitement.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_wsgi_application()
