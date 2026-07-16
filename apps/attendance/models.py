"""
Modèles de l'application attendance.

Suivi des absences et présences des élèves par cours et par jour.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.enums import UserRole
from apps.core.models.base import BaseModel


class Presence(BaseModel):
    """Enregistrement de présence/absence d'un élève pour un cours à une date donnée."""

    class Statut(models.TextChoices):
        PRESENT = "present", _("Présent")
        ABSENT = "absent", _("Absent")
        ABSENT_JUSTIFIE = "absent_justifie", _("Absent justifié")
        RETARD = "retard", _("Retard")

    eleve = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="presences",
        verbose_name=_("Élève"),
        limit_choices_to={"role": UserRole.ELEVE},
    )
    cours = models.ForeignKey(
        "academic.Cours",
        on_delete=models.CASCADE,
        related_name="presences",
        verbose_name=_("Cours"),
    )
    classe = models.ForeignKey(
        "academic.Classe",
        on_delete=models.CASCADE,
        related_name="presences",
        verbose_name=_("Classe"),
    )
    date = models.DateField(
        verbose_name=_("Date"),
    )
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.PRESENT,
        verbose_name=_("Statut"),
    )
    justification = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Justification"),
        help_text=_("Motif d'absence ou de retard"),
    )
    minutes_retard = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Minutes de retard"),
        help_text=_("0 si présent ou absent"),
    )
    enregistre_par = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="presences_enregistrees",
        verbose_name=_("Enregistré par"),
    )

    class Meta:
        verbose_name = _("Présence")
        verbose_name_plural = _("Présences")
        ordering = ["-date", "eleve__last_name", "eleve__first_name"]
        unique_together = [("eleve", "cours", "date")]
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["eleve", "date"]),
            models.Index(fields=["classe", "date"]),
            models.Index(fields=["statut"]),
        ]

    def __str__(self):
        return f"{self.eleve.full_name} — {self.date} — {self.get_statut_display()}"

    @property
    def est_absent(self):
        return self.statut in [self.Statut.ABSENT, self.Statut.ABSENT_JUSTIFIE]

    @property
    def est_retard(self):
        return self.statut == self.Statut.RETARD
