"""
Modèles de l'application students.

Notes des élèves et accès aux ressources.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models.base import BaseModel


class Note(BaseModel):
    """Note d'un élève pour une évaluation."""
    eleve = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="notes",
        verbose_name=_("Élève"),
        limit_choices_to={"role": "eleve"},
    )
    evaluation = models.ForeignKey(
        "academic.Evaluation",
        on_delete=models.CASCADE,
        related_name="notes",
        verbose_name=_("Évaluation"),
    )
    valeur = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Note obtenue"),
    )
    appreciation = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Appréciation"),
    )
    date_saisie = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de saisie"),
    )

    class Meta:
        verbose_name = _("Note")
        verbose_name_plural = _("Notes")
        ordering = ["-date_saisie"]
        unique_together = [("eleve", "evaluation")]

    def __str__(self):
        return f"{self.eleve.full_name} — {self.evaluation.titre} : {self.valeur}/{self.evaluation.sur}"

    @property
    def pourcentage(self):
        """Pourcentage de la note par rapport au maximum."""
        if self.evaluation.sur and self.evaluation.sur > 0:
            return (float(self.valeur) / float(self.evaluation.sur)) * 100
        return 0

    @property
    def mention(self):
        """Mention basée sur le pourcentage."""
        pct = self.pourcentage
        if pct >= 80:
            return "Très bien"
        elif pct >= 60:
            return "Bien"
        elif pct >= 50:
            return "Passable"
        else:
            return "Insuffisant"


class ResourceAccess(BaseModel):
    """Accès d'un élève à une ressource (après achat ou si gratuite)."""
    eleve = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="acces_ressources",
        verbose_name=_("Élève"),
    )
    ressource = models.ForeignKey(
        "marketplace.Resource",
        on_delete=models.CASCADE,
        related_name="acces",
        verbose_name=_("Ressource"),
    )
    commande = models.ForeignKey(
        "marketplace.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Commande associée"),
    )

    class Meta:
        verbose_name = _("Accès ressource")
        verbose_name_plural = _("Accès ressources")
        ordering = ["-created_at"]
        unique_together = [("eleve", "ressource")]

    def __str__(self):
        return f"{self.eleve.full_name} → {self.ressource.titre}"
