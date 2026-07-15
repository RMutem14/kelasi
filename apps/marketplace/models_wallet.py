"""
Modèles de portefeuille numérique pour les enseignants.

Wallet : stocke l'argent des ventes de ressources.
WithdrawalRequest : demandes de retrait vers mobile money.
"""
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.core.models.base import BaseModel


class Wallet(BaseModel):
    """Portefeuille numérique d'un enseignant."""
    enseignant = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="wallet",
        verbose_name=_("Enseignant"),
        limit_choices_to={"role": "enseignant"},
    )
    solde = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Solde"),
        help_text=_("Solde disponible en USD"),
    )
    total_gagne = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Total gagné"),
        help_text=_("Cumul de tous les gains"),
    )
    total_retire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Total retiré"),
        help_text=_("Cumul de tous les retraits"),
    )

    class Meta:
        verbose_name = _("Portefeuille")
        verbose_name_plural = "Portefeuilles"

    def __str__(self):
        return f"{self.enseignant.full_name} — {self.solde} $"

    def crediter(self, montant, description=""):
        """Crédite le wallet d'un montant (suite à une vente)."""
        from decimal import Decimal
        montant = Decimal(str(montant))
        self.solde += montant
        self.total_gagne += montant
        self.save(update_fields=["solde", "total_gagne", "updated_at"])
        WalletTransaction.objects.create(
            wallet=self,
            type=WalletTransaction.Type.CREDIT,
            montant=montant,
            description=description or "Vente de ressource",
        )

    def debiter(self, montant, description=""):
        """Débite le wallet d'un montant (suite à un retrait)."""
        from decimal import Decimal
        montant = Decimal(str(montant))
        if montant > self.solde:
            raise ValueError("Solde insuffisant pour ce retrait.")
        self.solde -= montant
        self.total_retire += montant
        self.save(update_fields=["solde", "total_retire", "updated_at"])
        WalletTransaction.objects.create(
            wallet=self,
            type=WalletTransaction.Type.DEBIT,
            montant=montant,
            description=description or "Retrait",
        )


class WalletTransaction(BaseModel):
    """Transaction d'un portefeuille (crédit ou débit)."""
    class Type(models.TextChoices):
        CREDIT = "credit", _("Crédit")
        DEBIT = "debit", _("Débit")

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("Portefeuille"),
    )
    type = models.CharField(
        max_length=10,
        choices=Type.choices,
        verbose_name=_("Type"),
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant"),
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name=_("Description"),
    )
    order = models.ForeignKey(
        "marketplace.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wallet_transactions",
        verbose_name=_("Commande associée"),
    )

    class Meta:
        verbose_name = _("Transaction de portefeuille")
        verbose_name_plural = _("Transactions de portefeuille")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_type_display()} {self.montant} $ — {self.description}"


class WithdrawalRequest(BaseModel):
    """Demande de retrait d'un enseignant vers mobile money."""
    class Operateur(models.TextChoices):
        ORANGE = "orange", _("Orange Money")
        AIRTEL = "airtel", _("Airtel Money")
        VODACOM = "vodacom", _("Vodacom M-Pesa")

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", _("En attente")
        APPROUVEE = "approuvee", _("Approuvée")
        REJETEE = "rejetee", _("Rejetée")
        PAYEE = "payee", _("Payée")

    enseignant = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="demandes_retrait",
        verbose_name=_("Enseignant"),
        limit_choices_to={"role": "enseignant"},
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant à retirer"),
    )
    operateur = models.CharField(
        max_length=20,
        choices=Operateur.choices,
        verbose_name=_("Opérateur"),
    )
    numero_telephone = models.CharField(
        max_length=20,
        verbose_name=_("Numéro de téléphone"),
        help_text=_("Numéro Mobile Money pour le transfert"),
    )
    utilise_numero_compte = models.BooleanField(
        default=False,
        verbose_name=_("Utiliser le numéro du compte"),
        help_text=_("True si l'enseignant a choisi son numéro de profil"),
    )
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE,
        verbose_name=_("Statut"),
    )
    note_admin = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Note admin"),
        help_text=_("Note interne lors de l'approbation/rejet"),
    )
    date_traitement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de traitement"),
    )

    class Meta:
        verbose_name = _("Demande de retrait")
        verbose_name_plural = _("Demandes de retrait")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.enseignant.full_name} — {self.montant} $ via {self.get_operateur_display()}"

    @property
    def est_en_attente(self):
        return self.statut == self.Statut.EN_ATTENTE
