"""
Service de paiement — orchestre les passerelles et les transactions.

Ce service est le point d'entrée unique pour tout paiement dans la
marketplace. Il :
1. Crée une Transaction (traçabilité)
2. Appelle la passerelle configurée
3. Met à jour la Transaction et l'Order selon le résultat
4. Envoie les notifications appropriées

Pour passer à un paiement réel :
1. Configurer la passerelle dans settings.MARKETPLACE_PAYMENT_GATEWAY
2. Implémenter les méthodes initiate_payment/verify_payment dans la classe
3. Créer un webhook view qui appelle PaymentService.verify_and_confirm()
"""
from django.utils import timezone
from django.conf import settings

from apps.marketplace.models import Order, Resource
from apps.marketplace.payments.gateways import get_payment_gateway, PaymentResult
from apps.marketplace.models import Transaction
from apps.core.constants import OrderStatus
from apps.students.models import ResourceAccess
from apps.notifications.models import Notification
from apps.core.constants import NotificationLevel


class PaymentService:
    """
    Service centralisé pour tous les paiements marketplace.

    Usage :
        service = PaymentService()
        result = service.process_payment(order=order, user=request.user)
        if result.success:
            # rediriger vers result.redirect_url si non vide
            # sinon le paiement est déjà confirmé
    """

    def __init__(self):
        self.gateway = get_payment_gateway()

    def process_payment(self, *, order: Order, user) -> PaymentResult:
        """
        Traite un paiement complet : initiate → verify → confirm.

        Pour la passerelle simulée, c'est immédiat.
        Pour une passerelle réelle, cette méthode retourne un redirect_url
        et la confirmation se fait via webhook (verify_and_confirm).

        Returns:
            PaymentResult
        """
        # 1. Créer la transaction (traçabilité)
        transaction = Transaction.objects.create(
            order=order,
            montant=order.montant,
            provider=self.gateway.name,
            statut=Transaction.Statut.INITIE,
            created_by=user,
        )

        # 2. Initier le paiement via la passerelle
        result = self.gateway.initiate_payment(order=order, user=user)

        # Mettre à jour la transaction
        transaction.reference_provider = result.provider_reference
        transaction.message = result.message

        if result.success:
            transaction.statut = Transaction.Statut.EN_COURS
            transaction.save(update_fields=["reference_provider", "message", "statut", "updated_at"])

            # Si la passerelle confirme immédiatement (simulation), on finalise
            if not result.redirect_url:
                return self._confirm_transaction(transaction, result, user)
            # Sinon, on retourne le redirect_url pour que l'utilisateur aille payer
            return result
        else:
            transaction.statut = Transaction.Statut.ECHOUE
            transaction.save(update_fields=["reference_provider", "message", "statut", "updated_at"])
            return result

    def verify_and_confirm(self, *, transaction_id: str, user=None) -> PaymentResult:
        """
        Vérifie un paiement auprès du fournisseur et confirme la commande.

        Appelée par :
        - Le webhook de la passerelle (après redirection utilisateur)
        - Un job de polling (optionnel)

        Returns:
            PaymentResult
        """
        try:
            transaction = Transaction.objects.get(reference_interne=transaction_id)
        except Transaction.DoesNotExist:
            # Peut-être une référence provider
            transaction = Transaction.objects.filter(reference_provider=transaction_id).first()
            if not transaction:
                return PaymentResult(success=False, message="Transaction introuvable.")

        if transaction.statut == Transaction.Statut.CONFIRME:
            return PaymentResult(
                success=True,
                transaction_id=str(transaction.reference_interne),
                message="Transaction déjà confirmée.",
            )

        result = self.gateway.verify_payment(transaction_id=transaction.reference_provider or str(transaction.reference_interne))

        if result.success:
            return self._confirm_transaction(transaction, result, user)
        else:
            transaction.statut = Transaction.Statut.ECHOUE
            transaction.message = result.message
            transaction.save(update_fields=["statut", "message", "updated_at"])
            return result

    def _confirm_transaction(self, transaction: Transaction, result: PaymentResult, user=None) -> PaymentResult:
        """Finalise une transaction confirmée : met à jour order, crée l'accès, notifie."""
        transaction.statut = Transaction.Statut.CONFIRME
        transaction.message = result.message
        transaction.save(update_fields=["statut", "message", "updated_at"])

        order = transaction.order
        order.statut = OrderStatus.PAYE
        order.save(update_fields=["statut", "updated_at"])

        # Donner l'accès à la ressource
        ResourceAccess.objects.get_or_create(
            eleve=order.eleve,
            ressource=order.ressource,
            defaults={"commande": order, "created_by": user or order.eleve},
        )

        # Notifier l'enseignant
        Notification.objects.create(
            destinataire=order.ressource.auteur,
            titre="Nouvelle vente",
            message=f"{order.eleve.full_name} a acheté votre ressource '{order.ressource.titre}' pour {order.montant} $.",
            niveau=NotificationLevel.SUCCESS,
            url=f"/marketplace/{order.ressource.pk}/",
        )

        # Notifier l'élève
        Notification.objects.create(
            destinataire=order.eleve,
            titre="Achat confirmé",
            message=f"Votre achat de '{order.ressource.titre}' est confirmé. Vous pouvez le télécharger.",
            niveau=NotificationLevel.SUCCESS,
            url=f"/marketplace/{order.ressource.pk}/telecharger/",
        )

        return PaymentResult(
            success=True,
            transaction_id=str(transaction.reference_interne),
            message="Paiement confirmé avec succès.",
        )
