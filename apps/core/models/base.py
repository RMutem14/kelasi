"""
Modèles abstraits de base pour l'ensemble du projet Huduma.

Tous les modèles métier héritent de ``BaseModel`` qui combine :
- UUID comme clé primaire
- Horodatage (created_at, updated_at)
- Audit (created_by, updated_by)
- Soft delete (deleted_at) avec managers dédiés

Ne jamais dupliquer ces briques dans une autre application.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """Ajoute ``created_at`` et ``updated_at`` auto-gérés."""

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Créé le"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Mis à jour le"),
    )

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Clé primaire UUID, non éditable, indexée."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )

    class Meta:
        abstract = True


class AuditModel(models.Model):
    """
    Traçabilité : qui a créé et qui a modifié l'enregistrement.

    Les deux champs pointent vers le modèle utilisateur personnalisé.
    Ils sont null=True pour permettre la création par des fixtures ou
    des scripts sans utilisateur authentifié.
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
        verbose_name=_("Créé par"),
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
        verbose_name=_("Modifié par"),
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Soft delete : marque l'enregistrement comme supprimé sans le retirer
    physiquement de la base. Utilise ``ActiveManager`` par défaut pour
    exclure automatiquement les enregistrements supprimés.
    """

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Supprimé le"),
    )

    # Import ici pour éviter la circularité au chargement du module
    # (ActiveManager est défini dans apps.core.managers)
    from apps.core.managers import ActiveManager
    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        """Marque l'enregistrement comme supprimé."""
        self.deleted_at = timezone.now()
        if user and user.is_authenticated:
            self.updated_by = user
        self.save(update_fields=["deleted_at", "updated_by"])

    def restore(self):
        """Annule le soft delete."""
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])

    @property
    def is_deleted(self):
        """Indique si l'enregistrement est marqué comme supprimé."""
        return self.deleted_at is not None


class BaseModel(TimeStampedModel, UUIDModel, AuditModel, SoftDeleteModel):
    """
    Modèle de base à utiliser pour tous les modèles métier.

    Combine UUID + horodatage + audit + soft delete.
    Hérite de quatre mixins abstraits, aucun champ supplémentaire.
    """

    class Meta:
        abstract = True
