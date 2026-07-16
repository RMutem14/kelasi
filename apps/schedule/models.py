"""
Modèles de l'application schedule.

Emploi du temps : créneaux hebdomadaires par classe et cours.
Détection automatique des conflits (prof/classe/salle).
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models.base import BaseModel


class Creneau(BaseModel):
    """Créneau hebdomadaire d'un cours dans l'emploi du temps."""

    class Jour(models.TextChoices):
        LUNDI = "lundi", _("Lundi")
        MARDI = "mardi", _("Mardi")
        MERCREDI = "mercredi", _("Mercredi")
        JEUDI = "jeudi", _("Jeudi")
        VENDREDI = "vendredi", _("Vendredi")
        SAMEDI = "samedi", _("Samedi")

    classe = models.ForeignKey(
        "academic.Classe",
        on_delete=models.CASCADE,
        related_name="creneaux",
        verbose_name=_("Classe"),
    )
    cours = models.ForeignKey(
        "academic.Cours",
        on_delete=models.CASCADE,
        related_name="creneaux",
        verbose_name=_("Cours"),
    )
    enseignant = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="creneaux_enseignant",
        verbose_name=_("Enseignant"),
    )
    jour = models.CharField(
        max_length=10,
        choices=Jour.choices,
        verbose_name=_("Jour"),
    )
    heure_debut = models.TimeField(
        verbose_name=_("Heure de début"),
    )
    heure_fin = models.TimeField(
        verbose_name=_("Heure de fin"),
    )
    salle = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name=_("Salle"),
    )
    annee_scolaire = models.ForeignKey(
        "academic.AnneeScolaire",
        on_delete=models.CASCADE,
        related_name="creneaux",
        verbose_name=_("Année scolaire"),
    )

    class Meta:
        verbose_name = _("Créneau")
        verbose_name_plural = _("Créneaux")
        ordering = ["jour", "heure_debut"]
        unique_together = [("classe", "jour", "heure_debut", "annee_scolaire")]
        indexes = [
            models.Index(fields=["jour", "heure_debut"]),
            models.Index(fields=["annee_scolaire", "jour"]),
            models.Index(fields=["enseignant", "jour"]),
        ]

    def __str__(self):
        return f"{self.classe.nom} — {self.cours.nom} — {self.get_jour_display()} {self.heure_debut}-{self.heure_fin}"

    @property
    def duree_minutes(self):
        """Durée du créneau en minutes."""
        from datetime import datetime
        debut = datetime.combine(datetime.today(), self.heure_debut)
        fin = datetime.combine(datetime.today(), self.heure_fin)
        return int((fin - debut).total_seconds() / 60)

    def detecter_conflits(self, exclude_pk=None):
        """Détecte les conflits pour ce créneau.

        Returns:
            list[dict]: liste des conflits trouvés.
        """
        conflits = []
        qs = Creneau.objects.filter(
            jour=self.jour,
            annee_scolaire=self.annee_scolaire,
        )
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)

        for other in qs:
            # Chevauchement horaire
            if self.heure_debut < other.heure_fin and self.heure_fin > other.heure_debut:
                # Conflit enseignant
                if other.enseignant_id == self.enseignant_id:
                    conflits.append({
                        "type": "enseignant",
                        "creneau": other,
                        "message": f"L'enseignant {self.enseignant.full_name} est déjà assigné à {other.classe.nom} — {other.cours.nom}",
                    })
                # Conflit classe
                if other.classe_id == self.classe_id:
                    conflits.append({
                        "type": "classe",
                        "creneau": other,
                        "message": f"La classe {self.classe.nom} a déjà {other.cours.nom} à cette heure",
                    })
                # Conflit salle
                if self.salle and other.salle and self.salle == other.salle:
                    conflits.append({
                        "type": "salle",
                        "creneau": other,
                        "message": f"La salle {self.salle} est déjà occupée par {other.classe.nom}",
                    })

        return conflits
