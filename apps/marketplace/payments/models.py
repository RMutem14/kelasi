"""
Modèle Transaction pour tracer tous les paiements.

Chaque tentative de paiement (réussie ou échouée) crée une Transaction.
Cela garantit une traçabilité complète pour les futurs audits et
la comptabilité.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models.base import BaseModel


class Transaction(BaseModel):
    """Transaction de paiement (traçabilité complète)."""

    class Statut(models.TextChoices):
        INITIE = "initie", _("Initié")
        EN_COURS = "en_cours", _("En cours")
        CONFIRME = "confirme", _("Confirmé")
        ECHOUE = "echoue", _("Échoué")
        REMBOURSE = "rembourse", _("Remboursé")

    order = models.ForeignKey(
        "marketplace.Order",
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
        help_text="simulated, orange_money, mpesa, ikeepay",
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
