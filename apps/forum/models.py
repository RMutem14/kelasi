"""
Modèles de l'application forum.

Questions/Réponses entre élèves et enseignants, par cours.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.enums import UserRole
from apps.core.models.base import BaseModel


class Question(BaseModel):
    """Question posée par un élève sur un cours."""

    class Statut(models.TextChoices):
        OUVERTE = "ouverte", _("Ouverte")
        FERMEE = "fermee", _("Fermée")
        REPONDUE = "repondue", _("Répondue")

    titre = models.CharField(
        max_length=200,
        verbose_name=_("Titre"),
    )
    contenu = models.TextField(
        verbose_name=_("Contenu"),
        help_text=_("Description détaillée de la question"),
    )
    auteur = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="questions_posees",
        verbose_name=_("Auteur"),
        limit_choices_to={"role": UserRole.ELEVE},
    )
    cours = models.ForeignKey(
        "academic.Cours",
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name=_("Cours"),
        null=True,
        blank=True,
    )
    statut = models.CharField(
        max_length=10,
        choices=Statut.choices,
        default=Statut.OUVERTE,
        verbose_name=_("Statut"),
    )
    vue_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Nombre de vues"),
    )

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["statut"]),
            models.Index(fields=["cours"]),
        ]

    def __str__(self):
        return f"{self.titre} — {self.auteur.full_name}"

    @property
    def nb_reponses(self):
        return self.reponses.count()

    @property
    def a_une_reponse_enseignant(self):
        return self.reponses.filter(auteur__role=UserRole.ENSEIGNANT).exists()


class Reponse(BaseModel):
    """Réponse à une question (par un enseignant ou un élève)."""

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="reponses",
        verbose_name=_("Question"),
    )
    auteur = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="reponses_donnees",
        verbose_name=_("Auteur"),
    )
    contenu = models.TextField(
        verbose_name=_("Contenu"),
    )
    est_validee = models.BooleanField(
        default=False,
        verbose_name=_("Réponse validée"),
        help_text=_("Marquée comme correcte par l'auteur de la question"),
    )

    class Meta:
        verbose_name = _("Réponse")
        verbose_name_plural = _("Réponses")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["est_validee"]),
        ]

    def __str__(self):
        return f"Réponse à '{self.question.titre}' — {self.auteur.full_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Marquer la question comme répondue si la réponse vient d'un enseignant
        if self.auteur.is_teacher and self.question.statut == Question.Statut.OUVERTE:
            self.question.statut = Question.Statut.REPONDUE
            self.question.save(update_fields=["statut"])
