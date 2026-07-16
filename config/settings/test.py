"""
Settings de test.

Hérite de dev et applique un patch de compatibilité Python 3.14
pour Django 5.1 (Context.__copy__).
"""

# Monkey-patch: Django 5.1 Context.__copy__ fails on Python 3.14
# because dict no longer has __copy__. We provide a compatible version.
from django.template.context import Context as _Context

def _patched_context_copy(self):
    duplicate = object.__new__(self.__class__)
    duplicate.dicts = self.dicts[:]
    return duplicate

if not hasattr(dict, "__copy__"):
    _Context.__copy__ = _patched_context_copy

from .dev import *  # noqa: F401,F403

# Utiliser SQLite en mémoire pour les tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Pas de debug en test
DEBUG = False

# Password hasher rapide pour les tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
