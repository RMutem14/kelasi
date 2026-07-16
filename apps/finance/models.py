"""
Modèles de l'application finance.

Frais de scolarité, paiements et suivi financier de l'établissement.
Adapté au contexte RDC : minerval, frais d'examen, frais de laboratoire, etc.
"""
from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accounts.enums import UserRole
from apps.core.models.base import BaseModel


class FraisType(BaseModel):
    """Type de frais scolaire (minerval, examen, laboratoire, etc.)."""

    class Categorie(models.TextChoices):
        SCOLARITE = "scolarite", _("Scolarité")
        EXAMEN = "examen", _("Examen")
        LABORATOIRE = "laboratoire", _("Laboratoire")
        ACTIVITE = "activite", _("Activité parascolaire")
        TRANSPORT = "transport", _("Transport")
        INTERNAT = "internat", _("Internat")
        AUTRE = "autre", _("Autre")

    libelle = models.CharField(
        max_length=100,
        verbose_name=_("Libellé"),
        help_text=_("Ex : Minerval 1er terme, Frais d'examen, Frais de labo"),
    )
    categorie = models.CharField(
        max_length=20,
        choices=Categorie.choices,
        default=Categorie.SCOLARITE,
        verbose_name=_("Catégorie"),
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant (USD)"),
    )
    annee_scolaire = models.ForeignKey(
        "academic.AnneeScolaire",
        on_delete=models.CASCADE,
        related_name="frais_types",
        verbose_name=_("Année scolaire"),
    )
    est_obligatoire = models.BooleanField(
        default=True,
        verbose_name=_("Obligatoire"),
    )
    est_recurrent = models.BooleanField(
        default=False,
        verbose_name=_("Récurrent"),
        help_text=_("True si le frais s'applique à chaque terme"),
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Description"),
    )

    class Meta:
        verbose_name = _("Type de frais")
        verbose_name_plural = _("Types de frais")
        ordering = ["annee_scolaire__date_debut", "categorie", "libelle"]

    def __str__(self):
        return f"{self.libelle} — {self.montant} $"


class FraisEleve(BaseModel):
    """Frais assigné à un élève pour une année scolaire.

    Généré automatiquement ou manuellement par l'admin.
    """

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", _("En attente")
        PARTIELLEMENT_PAYE = "partiellement_paye", _("Partiellement payé")
        PAYE = "paye", _("Payé")
        EN_RETARD = "en_retard", _("En retard")
        EXEMPT = "exempt", _("Exempté")

    eleve = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="frais",
        verbose_name=_("Élève"),
        limit_choices_to={"role": UserRole.ELEVE},
    )
    frais_type = models.ForeignKey(
        FraisType,
        on_delete=models.CASCADE,
        related_name="frais_eleves",
        verbose_name=_("Type de frais"),
    )
    annee_scolaire = models.ForeignKey(
        "academic.AnneeScolaire",
        on_delete=models.CASCADE,
        related_name="frais_eleves",
        verbose_name=_("Année scolaire"),
    )
    montant_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant total"),
    )
    montant_paye = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant payé"),
    )
    date_echeance = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date d'échéance"),
    )
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE,
        verbose_name=_("Statut"),
    )
    note = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Note"),
    )

    class Meta:
        verbose_name = _("Frais élève")
        verbose_name_plural = _("Frais élèves")
        ordering = ["-annee_scolaire__date_debut", "eleve__last_name", "eleve__first_name"]
        unique_together = [("eleve", "frais_type", "annee_scolaire")]
        indexes = [
            models.Index(fields=["statut"]),
            models.Index(fields=["annee_scolaire", "statut"]),
        ]

    def __str__(self):
        return f"{self.eleve.full_name} — {self.frais_type.libelle} ({self.get_statut_display()})"

    @property
    def montant_restant(self):
        """Montant restant à payer."""
        return self.montant_total - self.montant_paye

    @property
    def est_solde(self):
        """True si le frais est entièrement payé."""
        return self.montant_paye >= self.montant_total

    @property
    def pourcentage_paye(self):
        """Pourcentage du montant payé."""
        if self.montant_total > 0:
            return (float(self.montant_paye) / float(self.montant_total)) * 100
        return 0

    def mettre_a_jour_statut(self):
        """Met à jour le statut selon les paiements et l'échéance."""
        if self.statut == self.Statut.EXEMPT:
            return
        if self.est_solde:
            self.statut = self.Statut.PAYE
        elif self.montant_paye > 0:
            self.statut = self.Statut.PARTIELLEMENT_PAYE
        elif self.date_echeance and timezone.now().date() > self.date_echeance:
            self.statut = self.Statut.EN_RETARD
        else:
            self.statut = self.Statut.EN_ATTENTE

    def enregistrer_paiement(self, montant, methode="especes", reference="", enregistre_par=None):
        """Enregistre un paiement et met à jour le statut.

        Returns:
            Paiement: l'objet Paiement créé.
        """
        montant = Decimal(str(montant))
        self.montant_paye += montant
        self.mettre_a_jour_statut()
        self.save()

        paiement = Paiement.objects.create(
            frais_eleve=self,
            montant=montant,
            methode=methode,
            reference=reference,
            enregistre_par=enregistre_par,
        )
        return paiement


class Paiement(BaseModel):
    """Paiement effectué pour un frais scolaire."""

    class Methode(models.TextChoices):
        ESPECES = "especes", _("Espèces")
        MOBILE_MONEY = "mobile_money", _("Mobile Money")
        VIREMENT = "virement", _("Virement bancaire")
        AUTRE = "autre", _("Autre")

    frais_eleve = models.ForeignKey(
        FraisEleve,
        on_delete=models.CASCADE,
        related_name="paiements",
        verbose_name=_("Frais"),
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant"),
    )
    methode = models.CharField(
        max_length=20,
        choices=Methode.choices,
        default=Methode.ESPECES,
        verbose_name=_("Méthode de paiement"),
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name=_("Référence"),
        help_text=_("Numéro de transaction Mobile Money, reçu, etc."),
    )
    date_paiement = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de paiement"),
    )
    enregistre_par = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paiements_enregistres",
        verbose_name=_("Enregistré par"),
    )

    class Meta:
        verbose_name = _("Paiement")
        verbose_name_plural = _("Paiements")
        ordering = ["-date_paiement"]
        indexes = [
            models.Index(fields=["date_paiement"]),
            models.Index(fields=["methode", "date_paiement"]),
        ]

    def __str__(self):
        return f"{self.montant} $ — {self.frais_eleve.eleve.full_name} ({self.get_methode_display()})"

    @property
    def code(self):
        """Code d'identification du paiement."""
        return f"PAY-{str(self.id)[:8].upper()}"
