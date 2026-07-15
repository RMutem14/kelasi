"""
Modèles de l'application notifications.

Notifications internes persistées (pas de websocket pour le MVP).
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.constants import NotificationLevel
from apps.core.models.base import BaseModel


class Notification(BaseModel):
    """Notification interne adressée à un utilisateur."""
    destinataire = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Destinataire"),
    )
    titre = models.CharField(max_length=200, verbose_name=_("Titre"))
    message = models.TextField(verbose_name=_("Message"))
    niveau = models.CharField(
        max_length=20,
        choices=NotificationLevel.choices,
        default=NotificationLevel.INFO,
        verbose_name=_("Niveau"),
    )
    lu = models.BooleanField(
        default=False,
        verbose_name=_("Lu"),
    )
    url = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name=_("URL d'action"),
        help_text=_("URL vers laquelle rediriger au clic"),
    )

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.destinataire.full_name} — {self.titre}"

    @property
    def couleur(self):
        """Classe de couleur Tailwind selon le niveau."""
        return {
            NotificationLevel.INFO: "sky",
            NotificationLevel.SUCCESS: "emerald",
            NotificationLevel.WARNING: "amber",
            NotificationLevel.ERROR: "red",
        }.get(self.niveau, "slate")

    @property
    def icon(self):
        """Nom d'icône Lucide selon le niveau."""
        return {
            NotificationLevel.INFO: "info",
            NotificationLevel.SUCCESS: "check-circle",
            NotificationLevel.WARNING: "alert-triangle",
            NotificationLevel.ERROR: "x-circle",
        }.get(self.niveau, "bell")
