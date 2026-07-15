"""
Modèles de l'application academic.

Gestion des classes, des cours (matières) et des années scolaires.
Tous les modèles héritent de BaseModel (UUID + timestamps + audit + soft delete).
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.enums import UserRole
from apps.core.models.base import BaseModel


class AnneeScolaire(BaseModel):
    """Année scolaire (ex : 2026-2027)."""

    libelle = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Libellé"),
        help_text=_("Exemple : 2026-2027"),
    )
    date_debut = models.DateField(verbose_name=_("Date de début"))
    date_fin = models.DateField(verbose_name=_("Date de fin"))
    est_active = models.BooleanField(
        default=False,
        verbose_name=_("Année active"),
    )

    class Meta:
        verbose_name = _("Année scolaire")
        verbose_name_plural = _("Années scolaires")
        ordering = ["-date_debut"]

    def __str__(self):
        return self.libelle


class Classe(BaseModel):
    """Classe de l'établissement (ex : 5ème A, 6ème B)."""

    class Niveau(models.TextChoices):
        MATERNELLE = "maternelle", _("Maternelle")
        PRIMAIRE = "primaire", _("Primaire")
        SECONDAIRE = "secondaire", _("Secondaire")
        FINALISTE = "finaliste", _("Finaliste")

    class Statut(models.TextChoices):
        ACTIVE = "active", _("Active")
        SUSPENDUE = "suspendue", _("Suspendue")
        A_COMPLETER = "a_completer", _("À compléter")

    nom = models.CharField(max_length=50, verbose_name=_("Nom"))
    niveau = models.CharField(
        max_length=20,
        choices=Niveau.choices,
        default=Niveau.SECONDAIRE,
        verbose_name=_("Niveau"),
    )
    section = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name=_("Section"),
        help_text=_("Ex : scientifique, littéraire, pédagogique"),
    )
    titulaire = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="classes_titulaires",
        verbose_name=_("Titulaire"),
        limit_choices_to={"role": UserRole.ENSEIGNANT},
    )
    annee_scolaire = models.ForeignKey(
        AnneeScolaire,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Année scolaire"),
    )
    effectif = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Effectif"),
        help_text=_("Nombre d'élèves"),
    )
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.ACTIVE,
        verbose_name=_("Statut"),
    )

    class Meta:
        verbose_name = _("Classe")
        verbose_name_plural = _("Classes")
        ordering = ["nom"]

    def __str__(self):
        return self.nom

    @property
    def initials(self):
        """Initiales pour l'avatar (ex : 5A pour 5ème A)."""
        parts = self.nom.replace("ème", "").replace("er", "").split()
        return "".join(p[0].upper() for p in parts if p)[:2]


class Cours(BaseModel):
    """Cours / matière enseignée (ex : Mathématiques, Français)."""

    class Statut(models.TextChoices):
        ACTIF = "actif", _("Actif")
        SANS_ENSEIGNANT = "sans_enseignant", _("Sans enseignant")
        A_COMPLETER = "a_completer", _("À compléter")

    nom = models.CharField(max_length=100, verbose_name=_("Nom du cours"))
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Code"),
        help_text=_("Ex : MATH, FR, PHYS"),
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Description"),
    )
    enseignant = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cours_enseignes",
        verbose_name=_("Enseignant"),
        limit_choices_to={"role": UserRole.ENSEIGNANT},
    )
    classe = models.ForeignKey(
        Classe,
        on_delete=models.CASCADE,
        related_name="cours",
        verbose_name=_("Classe"),
    )
    coefficient = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Coefficient"),
    )
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.ACTIF,
        verbose_name=_("Statut"),
    )

    class Meta:
        verbose_name = _("Cours")
        verbose_name_plural = _("Cours")
        ordering = ["classe__nom", "nom"]
        unique_together = [("classe", "code")]

    def __str__(self):
        return f"{self.nom} ({self.classe.nom})"


class Evaluation(BaseModel):
    """Évaluation (devoir, interrogation, examen)."""

    class Type(models.TextChoices):
        DEVOIR = "devoir", _("Devoir")
        INTERROGATION = "interrogation", _("Interrogation")
        EXAMEN = "examen", _("Examen")
        TP = "tp", _("Travail pratique")

    class Statut(models.TextChoices):
        PROGRAMMEE = "programmee", _("Programmée")
        EN_COURS = "en_cours", _("En cours")
        TERMINEE = "terminee", _("Terminée")
        CORRIGEE = "corrigee", _("Corrigée")

    titre = models.CharField(max_length=200, verbose_name=_("Titre"))
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.DEVOIR,
        verbose_name=_("Type"),
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Description"),
    )
    enseignant = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="evaluations_creees",
        verbose_name=_("Enseignant"),
    )
    classe = models.ForeignKey(
        Classe,
        on_delete=models.CASCADE,
        related_name="evaluations",
        verbose_name=_("Classe"),
    )
    cours = models.ForeignKey(
        Cours,
        on_delete=models.CASCADE,
        related_name="evaluations",
        verbose_name=_("Cours"),
    )
    date_evaluation = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date d'évaluation"),
    )
    duree_minutes = models.PositiveIntegerField(
        default=60,
        verbose_name=_("Durée (minutes)"),
    )
    sur = models.PositiveIntegerField(
        default=20,
        verbose_name=_("Sur"),
        help_text=_("Note maximale (ex : 20)"),
    )
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.PROGRAMMEE,
        verbose_name=_("Statut"),
    )

    class Meta:
        verbose_name = _("Évaluation")
        verbose_name_plural = _("Évaluations")
        ordering = ["-date_evaluation"]

    def __str__(self):
        return f"{self.titre} ({self.classe.nom})"
