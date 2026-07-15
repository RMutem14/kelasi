"""
Managers personnalisés pour le soft delete.

``ActiveManager`` exclut automatiquement les enregistrements supprimés
(deleted_at IS NULL). C'est le manager par défaut de tous les modèles
qui héritent de ``SoftDeleteModel``.

``AllObjectsManager`` retourne tous les enregistrements, y compris
supprimés. À utiliser avec parcimonie (administration, audits).
"""
from django.db import models


class ActiveManager(models.Manager):
    """Manager par défaut : exclut les enregistrements soft-deleted."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager):
    """Manager alternatif : retourne tous les enregistrements."""

    def get_queryset(self):
        return super().get_queryset()
