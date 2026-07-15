"""
Modèles de l'application marketplace.

Ressources pédagogiques commercialisables, achats et téléchargements.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.constants import PublicationStatus, OrderStatus, ResourceType, ResourceCategory
from apps.core.models.base import BaseModel


class Resource(BaseModel):
    """Ressource pédagogique commercialisable publiée par un enseignant."""
    titre = models.CharField(max_length=200, verbose_name=_("Titre"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    auteur = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="ressources_publiees",
        verbose_name=_("Auteur"),
        limit_choices_to={"role": "enseignant"},
    )
    classe = models.ForeignKey(
        "academic.Classe",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ressources",
        verbose_name=_("Classe"),
    )
    cours = models.ForeignKey(
        "academic.Cours",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ressources",
        verbose_name=_("Cours"),
    )
    type = models.CharField(
        max_length=20,
        choices=ResourceType.choices,
        default=ResourceType.SYLLABUS,
        verbose_name=_("Type"),
    )
    categorie = models.CharField(
        max_length=20,
        choices=ResourceCategory.choices,
        default=ResourceCategory.COURS,
        verbose_name=_("Catégorie"),
    )
    prix = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name=_("Prix (USD)"),
        help_text=_("0 pour gratuit"),
    )
    fichier = models.FileField(
        upload_to="marketplace/ressources/",
        verbose_name=_("Fichier"),
        help_text=_("PDF ou DOCX"),
    )
    image_couverture = models.ImageField(
        upload_to="marketplace/couvertures/",
        blank=True,
        null=True,
        verbose_name=_("Image de couverture"),
    )
    statut = models.CharField(
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.BROUILLON,
        verbose_name=_("Statut"),
    )
    nombre_vues = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de vues"))
    nombre_telechargements = models.PositiveIntegerField(default=0, verbose_name=_("Téléchargements"))

    class Meta:
        verbose_name = _("Ressource")
        verbose_name_plural = _("Ressources")
        ordering = ["-created_at"]

    def __str__(self):
        return self.titre

    @property
    def est_gratuit(self):
        return self.prix == 0


class Order(BaseModel):
    """Commande d'une ressource par un élève (paiement simulé)."""
    eleve = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="commandes",
        verbose_name=_("Élève"),
        limit_choices_to={"role": "eleve"},
    )
    ressource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="commandes",
        verbose_name=_("Ressource"),
    )
    montant = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_("Montant payé"),
    )
    statut = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.EN_ATTENTE,
        verbose_name=_("Statut"),
    )
    reference = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Référence"),
        blank=True,
    )

    class Meta:
        verbose_name = _("Commande")
        verbose_name_plural = _("Commandes")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.eleve.full_name} — {self.ressource.titre}"

    def save(self, *args, **kwargs):
        if not self.reference:
            import uuid
            self.reference = f"CMD-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class Download(BaseModel):
    """Téléchargement d'une ressource par un élève."""
    eleve = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="telechargements",
        verbose_name=_("Élève"),
    )
    ressource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="telechargements_log",
        verbose_name=_("Ressource"),
    )

    class Meta:
        verbose_name = _("Téléchargement")
        verbose_name_plural = _("Téléchargements")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.eleve.full_name} — {self.ressource.titre}"



class Transaction(BaseModel):
    """Transaction de paiement (traçabilité complète)."""

    class Statut(models.TextChoices):
        INITIE = "initie", _("Initié")
        EN_COURS = "en_cours", _("En cours")
        CONFIRME = "confirme", _("Confirmé")
        ECHOUE = "echoue", _("Échoué")
        REMBOURSE = "rembourse", _("Remboursé")

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("Commande"),
    )
    montant = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_("Montant"),
    )
    provider = models.CharField(
        max_length=30,
        verbose_name=_("Fournisseur de paiement"),
    )
    reference_interne = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Référence interne"),
        blank=True,
    )
    reference_provider = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name=_("Référence fournisseur"),
    )
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.INITIE,
        verbose_name=_("Statut"),
    )
    message = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Message"),
    )

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference_interne} — {self.montant} $ ({self.get_statut_display()})"

    def save(self, *args, **kwargs):
        if not self.reference_interne:
            import uuid
            self.reference_interne = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    @property
    def est_confirme(self):
        return self.statut == self.Statut.CONFIRME


# Importer les modèles wallet pour qu'ils soient découverts par Django
from apps.marketplace.models_wallet import Wallet, WalletTransaction, WithdrawalRequest  # noqa: F401, E402
