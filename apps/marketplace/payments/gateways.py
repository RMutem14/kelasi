"""
Couche d'abstraction pour les passerelles de paiement.

Cette architecture permet de basculer facilement entre la simulation
et une intégration réelle (Orange Money, M-Pesa, iKeePay, etc.)
en modifiant uniquement la variable d'environnement
``MARKETPLACE_PAYMENT_GATEWAY``.

Pour ajouter une nouvelle passerelle :
1. Créer une classe héritant de ``PaymentGateway``
2. Implémenter les méthodes ``initiate_payment`` et ``verify_payment``
3. L'enregistrer dans ``GATEWAY_REGISTRY``
4. Configurer le nom dans ``settings.MARKETPLACE_PAYMENT_GATEWAY``
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class PaymentResult:
    """Résultat d'une tentative de paiement."""
    success: bool
    transaction_id: str = ""
    provider_reference: str = ""
    message: str = ""
    redirect_url: str = ""
    metadata: dict = field(default_factory=dict)


class PaymentGateway(ABC):
    """
    Interface abstraite pour toutes les passerelles de paiement.

    Toutes les méthodes retournent un objet ``PaymentResult``.
    Les implémentations ne doivent JAMAIS lancer d'exception
    métier — elles doivent capturer les erreurs et les retourner
    dans ``PaymentResult.success = False``.
    """

    name: str = "base"

    @abstractmethod
    def initiate_payment(self, *, order, user) -> PaymentResult:
        """
        Initialise un paiement auprès du fournisseur.

        Args:
            order: L'objet Order à payer.
            user: L'utilisateur qui paie.

        Returns:
            PaymentResult avec success=True si l'initialisation a réussi,
            et redirect_url si un redirect est nécessaire (ex: page de paiement).
        """
        ...

    @abstractmethod
    def verify_payment(self, *, transaction_id: str) -> PaymentResult:
        """
        Vérifie le statut d'un paiement auprès du fournisseur.

        Appelée par le webhook ou par un polling client.

        Args:
            transaction_id: L'identifiant de transaction retourné par initiate_payment.

        Returns:
            PaymentResult avec success=True si le paiement est confirmé.
        """
        ...

    def refund(self, *, transaction_id: str, amount=None) -> PaymentResult:
        """
        Rembourse un paiement (optionnel — pas toutes les passerelles le supportent).

        Returns:
            PaymentResult avec success=True si le remboursement a réussi.
        """
        return PaymentResult(
            success=False,
            message=f"Les remboursements ne sont pas supportés par {self.name}.",
        )


# ============================================================
# Passerelle simulée (pour le MVP / démo jury)
# ============================================================

class SimulatedPaymentGateway(PaymentGateway):
    """
    Passerelle de paiement simulée.

    Simule un paiement réussi immédiatement — idéale pour le MVP
    et la démonstration devant le jury. Aucun appel réseau.
    """

    name = "simulated"

    def initiate_payment(self, *, order, user) -> PaymentResult:
        """Simule une initialisation de paiement réussie."""
        import uuid
        transaction_id = f"SIM-{uuid.uuid4().hex[:12].upper()}"
        return PaymentResult(
            success=True,
            transaction_id=transaction_id,
            provider_reference=transaction_id,
            message="Paiement simulé initialisé avec succès.",
            redirect_url="",  # Pas de redirect — paiement immédiat
            metadata={"simulated": True, "amount": str(order.montant)},
        )

    def verify_payment(self, *, transaction_id: str) -> PaymentResult:
        """Simule une vérification — toujours réussie pour les transactions SIM-."""
        if transaction_id.startswith("SIM-"):
            return PaymentResult(
                success=True,
                transaction_id=transaction_id,
                message="Paiement simulé confirmé.",
            )
        return PaymentResult(
            success=False,
            transaction_id=transaction_id,
            message="Transaction simulée introuvable.",
        )


# ============================================================
# Passerelles futures (stubs prêts à implémenter)
# ============================================================

class OrangeMoneyGateway(PaymentGateway):
    """
    Passerelle Orange Money (RDC).

    Pour activer : configurer les variables d'environnement :
    - ORANGE_MONEY_API_URL
    - ORANGE_MONEY_API_KEY
    - ORANGE_MONEY_MERCHANT_CODE
    - ORANGE_MONEY_CALLBACK_URL
    """
    name = "orange_money"

    def initiate_payment(self, *, order, user) -> PaymentResult:
        # TODO: Implémenter l'appel API Orange Money
        # 1. Appeler POST /api/v1/payments/initiate
        # 2. Récupérer le redirect_url ou le USSD code
        # 3. Retourner PaymentResult avec redirect_url
        return PaymentResult(
            success=False,
            message="Orange Money n'est pas encore configuré. Contactez l'administrateur.",
        )

    def verify_payment(self, *, transaction_id: str) -> PaymentResult:
        # TODO: Implémenter GET /api/v1/payments/{transaction_id}/status
        return PaymentResult(
            success=False,
            message="Orange Money n'est pas encore configuré.",
        )


class MpesaGateway(PaymentGateway):
    """
    Passerelle M-Pesa (Vodacom RDC).

    Pour activer : configurer les variables d'environnement :
    - MPESA_API_URL
    - MPESA_API_KEY
    - MPESA_SHORTCODE
    - MPESA_PASSKEY
    """
    name = "mpesa"

    def initiate_payment(self, *, order, user) -> PaymentResult:
        # TODO: Implémenter STK Push via l'API Daraja
        return PaymentResult(
            success=False,
            message="M-Pesa n'est pas encore configuré. Contactez l'administrateur.",
        )

    def verify_payment(self, *, transaction_id: str) -> PaymentResult:
        # TODO: Implémenter la vérification via callback
        return PaymentResult(
            success=False,
            message="M-Pesa n'est pas encore configuré.",
        )


class IKeePayGateway(PaymentGateway):
    """
    Passerelle iKeePay.

    Pour activer : configurer les variables d'environnement :
    - IKEEPAY_API_URL
    - IKEEPAY_API_KEY
    - IKEEPAY_SECRET
    """
    name = "ikeepay"

    def initiate_payment(self, *, order, user) -> PaymentResult:
        # TODO: Implémenter l'appel API iKeePay
        return PaymentResult(
            success=False,
            message="iKeePay n'est pas encore configuré. Contactez l'administrateur.",
        )

    def verify_payment(self, *, transaction_id: str) -> PaymentResult:
        # TODO: Implémenter la vérification
        return PaymentResult(
            success=False,
            message="iKeePay n'est pas encore configuré.",
        )


# ============================================================
# Registre des passerelles
# ============================================================

GATEWAY_REGISTRY = {
    "simulated": SimulatedPaymentGateway,
    "orange_money": OrangeMoneyGateway,
    "mpesa": MpesaGateway,
    "ikeepay": IKeePayGateway,
}


def get_payment_gateway() -> PaymentGateway:
    """
    Factory : retourne l'instance de passerelle configurée.

    La passerelle est déterminée par ``settings.MARKETPLACE_PAYMENT_GATEWAY``.
    Par défaut : "simulated".

    Usage :
        from apps.marketplace.payments import get_payment_gateway
        gateway = get_payment_gateway()
        result = gateway.initiate_payment(order=order, user=request.user)
    """
    from django.conf import settings
    gateway_name = getattr(settings, "MARKETPLACE_PAYMENT_GATEWAY", "simulated")
    gateway_class = GATEWAY_REGISTRY.get(gateway_name, SimulatedPaymentGateway)
    return gateway_class()
