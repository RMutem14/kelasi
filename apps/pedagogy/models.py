"""
Modèles de l'application pedagogy.

Documents pédagogiques créés par les enseignants :
- Fiche de préparation
- Fiche de prévision
- Journal de classe
- Cahier de composition
- Cahier des cotes

Le workflow de validation est géré par l'application validation.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.constants import DocumentStatus
from apps.core.models.base import BaseModel


class DocumentPedagogique(BaseModel):
    """Document pédagogique créé par un enseignant."""

    class Type(models.TextChoices):
        FICHE_PREPARATION = "fiche_preparation", _("Fiche de préparation")
        FICHE_PREVISION = "fiche_prevision", _("Fiche de prévision")
        JOURNAL_CLASSE = "journal_classe", _("Journal de classe")
        CAHIER_COMPOSITION = "cahier_composition", _("Cahier de composition")
        CAHIER_COTES = "cahier_cotes", _("Cahier des cotes")

    titre = models.CharField(
        max_length=200,
        verbose_name=_("Titre"),
    )
    type = models.CharField(
        max_length=30,
        choices=Type.choices,
        verbose_name=_("Type de document"),
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Description"),
    )
    fichier = models.FileField(
        upload_to="documents/pedagogiques/",
        blank=True,
        null=True,
        verbose_name=_("Fichier"),
        help_text=_("PDF ou DOCX"),
    )
    auteur = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="documents_crees",
        verbose_name=_("Auteur"),
    )
    classe = models.ForeignKey(
        "academic.Classe",
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("Classe"),
    )
    cours = models.ForeignKey(
        "academic.Cours",
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("Cours"),
    )
    statut = models.CharField(
        max_length=20,
        choices=DocumentStatus.choices,
        default=DocumentStatus.BROUILLON,
        verbose_name=_("Statut"),
    )
    observation_directeur = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Observation du directeur"),
    )
    date_soumission = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de soumission"),
    )
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de validation"),
    )

    class Meta:
        verbose_name = _("Document pédagogique")
        verbose_name_plural = _("Documents pédagogiques")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.titre} ({self.get_type_display()})"

    @property
    def code(self):
        """Code d'identification du document (ex : DOC-001)."""
        return f"DOC-{str(self.id)[:8].upper()}"

    @property
    def can_be_validated(self):
        """True si le document est en attente de validation par le directeur."""
        return self.statut in [
            DocumentStatus.SOUMIS,
            DocumentStatus.CORRECTION,
        ]
