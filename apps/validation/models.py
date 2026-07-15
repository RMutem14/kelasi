"""
Modèles de l'application validation.

Historique des actions de validation sur les documents pédagogiques.
Chaque action (soumission, validation, rejet, demande de correction)
crée une entrée dans ValidationHistory.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.constants import DocumentStatus
from apps.core.models.base import BaseModel


class ValidationHistory(BaseModel):
    """Historique des actions de validation sur un document."""

    document = models.ForeignKey(
        "pedagogy.DocumentPedagogique",
        on_delete=models.CASCADE,
        related_name="historique_validation",
        verbose_name=_("Document"),
    )
    action_par = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="actions_validation",
        verbose_name=_("Action effectuée par"),
    )
    action = models.CharField(
        max_length=20,
        choices=DocumentStatus.choices,
        verbose_name=_("Action"),
    )
    commentaire = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Commentaire"),
    )

    class Meta:
        verbose_name = _("Historique de validation")
        verbose_name_plural = _("Historiques de validation")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.document.titre} — {self.get_action_display()} par {self.action_par}"
