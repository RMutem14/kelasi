"""
Signal pour créditer automatiquement le wallet de l'enseignant
lorsqu'une commande est confirmée (payée).
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.constants import OrderStatus
from apps.marketplace.models import Order
from apps.marketplace.models_wallet import Wallet


@receiver(post_save, sender=Order)
def credit_wallet_on_sale(sender, instance, created, **kwargs):
    """Crédite le wallet de l'enseignant quand une commande est payée."""
    if instance.statut != OrderStatus.PAYE:
        return

    # Éviter les double crédits : vérifier si une transaction wallet existe déjà
    from apps.marketplace.models_wallet import WalletTransaction
    existing = WalletTransaction.objects.filter(order=instance).exists()
    if existing:
        return

    # Récupérer ou créer le wallet de l'enseignant
    wallet, _ = Wallet.objects.get_or_create(
        enseignant=instance.ressource.auteur,
        defaults={},
    )

    # Créditer le montant de la vente
    wallet.crediter(
        montant=instance.montant,
        description=f"Vente — '{instance.ressource.titre}' (acheteur : {instance.eleve.full_name})",
    )

    # Lier la transaction à la commande
    last_tx = wallet.transactions.filter(
        type=WalletTransaction.Type.CREDIT
    ).first()
    if last_tx:
        last_tx.order = instance
        last_tx.save(update_fields=["order"])
