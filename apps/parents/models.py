"""
Modèles de l'application parents.

Liaison entre parents/tuteurs et élèves, avec gestion des relations
(père, mère, tuteur, oncle, etc.) et des droits d'accès.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.enums import UserRole
from apps.core.models.base import BaseModel


class ParentEleve(BaseModel):
    """Liaison entre un parent/tuteur et un élève.

    Un parent peut avoir plusieurs enfants.
    Un élève peut avoir plusieurs parents (père, mère, tuteur).
    """

    class Relation(models.TextChoices):
        PERE = "pere", _("Père")
        MERE = "mere", _("Mère")
        TUTEUR = "tuteur", _("Tuteur légal")
        ONCLE = "oncle", _("Oncle")
        TANTE = "tante", _("Tante")
        GRAND_PARENT = "grand_parent", _("Grand-parent")
        FRERE = "frere", _("Frère aîné")
        SŒUR = "soeur", _("Sœur aînée")
        AUTRE = "autre", _("Autre")

    parent = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="enfants_charge",
        verbose_name=_("Parent"),
        limit_choices_to={"role": UserRole.PARENT},
    )
    eleve = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="parents_charge",
        verbose_name=_("Élève"),
        limit_choices_to={"role": UserRole.ELEVE},
    )
    relation = models.CharField(
        max_length=20,
        choices=Relation.choices,
        default=Relation.TUTEUR,
        verbose_name=_("Relation"),
    )
    est_contact_principal = models.BooleanField(
        default=False,
        verbose_name=_("Contact principal"),
        help_text=_("Reçoit les notifications en priorité"),
    )
    autorise_consultation = models.BooleanField(
        default=True,
        verbose_name=_("Autorisé à consulter"),
        help_text=_("Notes, bulletins, absences, frais de scolarité"),
    )

    class Meta:
        verbose_name = _("Liaison parent-élève")
        verbose_name_plural = _("Liaisons parent-élève")
        ordering = ["eleve__last_name", "eleve__first_name", "relation"]
        unique_together = [("parent", "eleve")]

    def __str__(self):
        return f"{self.parent.full_name} → {self.eleve.full_name} ({self.get_relation_display()})"
