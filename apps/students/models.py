"""
Modèles de l'application students.

Notes des élèves, accès aux ressources, périodes et bulletins.
"""
from decimal import Decimal

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


# ============================================================
# BULLETINS DE NOTES (format EPST RDC)
# ============================================================


class Periode(BaseModel):
    """Période d'évaluation (1er terme, 2e terme, 3e terme/examen)."""

    class Ordre(models.IntegerChoices):
        PREMIER_TERME = 1, _("1er terme")
        DEUXIEME_TERME = 2, _("2e terme")
        TROISIEME_TERME = 3, _("3e terme / Examen")

    libelle = models.CharField(
        max_length=50,
        verbose_name=_("Libellé"),
        help_text=_("Ex : 1er terme, 2e terme, Examen final"),
    )
    ordre = models.PositiveSmallIntegerField(
        choices=Ordre.choices,
        verbose_name=_("Ordre"),
    )
    annee_scolaire = models.ForeignKey(
        "academic.AnneeScolaire",
        on_delete=models.CASCADE,
        related_name="periodes",
        verbose_name=_("Année scolaire"),
    )
    date_debut = models.DateField(verbose_name=_("Date de début"))
    date_fin = models.DateField(verbose_name=_("Date de fin"))
    est_active = models.BooleanField(
        default=False,
        verbose_name=_("Période active"),
    )

    class Meta:
        verbose_name = _("Période")
        verbose_name_plural = _("Périodes")
        ordering = ["annee_scolaire__date_debut", "ordre"]
        unique_together = [("annee_scolaire", "ordre")]

    def __str__(self):
        return f"{self.libelle} ({self.annee_scolaire.libelle})"


class Bulletin(BaseModel):
    """Bulletin de notes d'un élève pour une période donnée."""

    class Statut(models.TextChoices):
        BROUILLON = "brouillon", _("Brouillon")
        PUBLIE = "publie", _("Publié")
        ARCHIVE = "archive", _("Archivé")

    eleve = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="bulletins",
        verbose_name=_("Élève"),
        limit_choices_to={"role": "eleve"},
    )
    classe = models.ForeignKey(
        "academic.Classe",
        on_delete=models.CASCADE,
        related_name="bulletins",
        verbose_name=_("Classe"),
    )
    periode = models.ForeignKey(
        Periode,
        on_delete=models.CASCADE,
        related_name="bulletins",
        verbose_name=_("Période"),
    )
    annee_scolaire = models.ForeignKey(
        "academic.AnneeScolaire",
        on_delete=models.CASCADE,
        related_name="bulletins",
        verbose_name=_("Année scolaire"),
    )
    moyenne_generale = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_("Moyenne générale"),
        help_text=_("Moyenne sur 20"),
    )
    total_points = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name=_("Total des points"),
    )
    total_coefficients = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total des coefficients"),
    )
    rang = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Rang dans la classe"),
    )
    effectif_classe = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Effectif de la classe"),
    )
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.BROUILLON,
        verbose_name=_("Statut"),
    )
    date_publication = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de publication"),
    )
    publie_par = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bulletins_publies",
        verbose_name=_("Publié par"),
    )
    observation = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Observation générale"),
    )

    class Meta:
        verbose_name = _("Bulletin")
        verbose_name_plural = _("Bulletins")
        ordering = ["-periode__ordre", "eleve__last_name", "eleve__first_name"]
        unique_together = [("eleve", "periode")]

    def __str__(self):
        return f"Bulletin {self.eleve.full_name} — {self.periode.libelle}"

    @property
    def mention(self):
        """Mention basée sur la moyenne générale (système RDC)."""
        moy = float(self.moyenne_generale)
        if moy >= 16:
            return "Très Bien"
        elif moy >= 14:
            return "Bien"
        elif moy >= 12:
            return "Assez Bien"
        elif moy >= 10:
            return "Passable"
        else:
            return "Insuffisant"

    @property
    def est_publie(self):
        return self.statut == self.Statut.PUBLIE

    @property
    def pourcentage(self):
        """Pourcentage de réussite."""
        return (float(self.moyenne_generale) / 20) * 100

    def calculer_moyenne(self):
        """Recalcule la moyenne générale à partir des lignes du bulletin."""
        lignes = self.lignes.all()
        if not lignes:
            self.moyenne_generale = Decimal("0")
            self.total_points = Decimal("0")
            self.total_coefficients = 0
            return
        total_points = Decimal("0")
        total_coef = 0
        for ligne in lignes:
            total_points += ligne.moyenne_cours * Decimal(str(ligne.coefficient))
            total_coef += ligne.coefficient
        self.total_points = total_points
        self.total_coefficients = total_coef
        if total_coef > 0:
            self.moyenne_generale = (total_points / Decimal(str(total_coef))).quantize(
                Decimal("0.01")
            )
        else:
            self.moyenne_generale = Decimal("0")

    def calculer_rang(self):
        """Calcule le rang de l'élève dans la classe pour cette période."""
        bulletins = Bulletin.objects.filter(
            classe=self.classe,
            periode=self.periode,
            statut__in=[self.Statut.BROUILLON, self.Statut.PUBLIE],
        ).order_by("-moyenne_generale")
        for i, bull in enumerate(bulletins, 1):
            if bull.pk == self.pk:
                self.rang = i
                break
        self.effectif_classe = bulletins.count()


class BulletinLine(BaseModel):
    """Ligne d'un bulletin (un cours avec sa moyenne et son coefficient)."""

    bulletin = models.ForeignKey(
        Bulletin,
        on_delete=models.CASCADE,
        related_name="lignes",
        verbose_name=_("Bulletin"),
    )
    cours = models.ForeignKey(
        "academic.Cours",
        on_delete=models.CASCADE,
        related_name="bulletin_lines",
        verbose_name=_("Cours"),
    )
    coefficient = models.PositiveIntegerField(
        verbose_name=_("Coefficient"),
        help_text=_("Snapshot du coefficient au moment de la génération"),
    )
    moyenne_cours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_("Moyenne du cours"),
        help_text=_("Moyenne sur 20"),
    )
    appreciation = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Appréciation"),
    )
    ordre = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Ordre d'affichage"),
    )

    class Meta:
        verbose_name = _("Ligne de bulletin")
        verbose_name_plural = _("Lignes de bulletin")
        ordering = ["ordre", "cours__nom"]
        unique_together = [("bulletin", "cours")]

    def __str__(self):
        return f"{self.cours.nom} — {self.moyenne_cours}/20 (coef {self.coefficient})"

    @property
    def points(self):
        """Points pondérés (moyenne × coefficient)."""
        return self.moyenne_cours * Decimal(str(self.coefficient))

    @property
    def mention_cours(self):
        """Mention basée sur la moyenne du cours."""
        moy = float(self.moyenne_cours)
        if moy >= 16:
            return "TB"
        elif moy >= 14:
            return "B"
        elif moy >= 12:
            return "AB"
        elif moy >= 10:
            return "P"
        else:
            return "I"
