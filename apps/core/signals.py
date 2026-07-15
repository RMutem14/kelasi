"""
Signaux pour les notifications automatiques.

Ces signaux écoutent les actions métier et créent automatiquement
des notifications pour les utilisateurs concernés.

Notifications automatiques implémentées :
1. Nouvel utilisateur créé → notif admin
2. Document soumis → notif directeurs des études
3. Document validé/rejeté/correction → notif enseignant auteur
4. Ressource publiée → notif tous les élèves (optionnel)
5. Note ajoutée → notif élève
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.accounts.enums import UserRole
from apps.accounts.models import User
from apps.core.constants import (
    DocumentStatus, PublicationStatus, NotificationLevel,
)
from apps.notifications.models import Notification


def _notify_users(users, titre, message, niveau=NotificationLevel.INFO, url=""):
    """Helper : envoie une notification à plusieurs utilisateurs."""
    for user in users:
        Notification.objects.get_or_create(
            destinataire=user,
            titre=titre,
            message=message,
            defaults={"niveau": niveau, "url": url},
        )


# ============================================================
# 1. Nouvel utilisateur créé → notifier l'admin
# ============================================================

@receiver(post_save, sender=User)
def notify_new_user(sender, instance, created, **kwargs):
    """Quand un nouvel utilisateur est créé, notifier tous les admins."""
    if not created:
        return
    admins = User.objects.filter(role=UserRole.ADMIN, is_active=True)
    _notify_users(
        admins,
        titre="Nouvel utilisateur créé",
        message=f"{instance.full_name} ({instance.email}) a rejoint la plateforme avec le rôle {instance.get_role_display()}.",
        niveau=NotificationLevel.INFO,
        url="/accounts/users/",
    )


# ============================================================
# 2. Document soumis → notifier les directeurs des études
# ============================================================

@receiver(post_save, sender="pedagogy.DocumentPedagogique")
def notify_document_status_change(sender, instance, created, **kwargs):
    """
    Notifie les directeurs quand un document est soumis,
    et notifie l'enseignant quand le statut change (validation/rejet/correction).
    """
    if created:
        return  # Pas de notif à la création (brouillon par défaut)

    # Document soumis → notifier les directeurs
    if instance.statut == DocumentStatus.SOUMIS:
        directeurs = User.objects.filter(role=UserRole.DIRECTEUR_ETUDES, is_active=True)
        _notify_users(
            directeurs,
            titre="Nouveau document à valider",
            message=f"{instance.auteur.full_name} a soumis '{instance.titre}' ({instance.get_type_display()}).",
            niveau=NotificationLevel.WARNING,
            url="/validation/documents/",
        )

    # Document validé → notifier l'enseignant
    elif instance.statut == DocumentStatus.VALIDE:
        Notification.objects.get_or_create(
            destinataire=instance.auteur,
            titre="Document validé",
            message=f"Votre document '{instance.titre}' a été validé par le directeur des études.",
            defaults={"niveau": NotificationLevel.SUCCESS, "url": "/pedagogy/"},
        )

    # Document rejeté → notifier l'enseignant
    elif instance.statut == DocumentStatus.REJETE:
        Notification.objects.get_or_create(
            destinataire=instance.auteur,
            titre="Document rejeté",
            message=f"Votre document '{instance.titre}' a été rejeté. Consultez l'observation du directeur.",
            defaults={"niveau": NotificationLevel.ERROR, "url": "/pedagogy/"},
        )

    # Correction demandée → notifier l'enseignant
    elif instance.statut == DocumentStatus.CORRECTION:
        Notification.objects.get_or_create(
            destinataire=instance.auteur,
            titre="Correction demandée",
            message=f"Une correction est demandée pour votre document '{instance.titre}'.",
            defaults={"niveau": NotificationLevel.WARNING, "url": "/pedagogy/"},
        )


# ============================================================
# 3. Ressource publiée → notifier tous les élèves
# ============================================================

@receiver(post_save, sender="marketplace.Resource")
def notify_resource_published(sender, instance, created, **kwargs):
    """Quand une ressource est publiée, notifier tous les élèves."""
    if instance.statut != PublicationStatus.PUBLIE:
        return
    # Éviter les doublons : ne notifier que si aucune notif n'existe déjà pour cette ressource
    existing = Notification.objects.filter(
        titre="Nouvelle ressource disponible",
        message__contains=instance.titre,
    ).exists()
    if existing:
        return

    eleves = User.objects.filter(role=UserRole.ELEVE, is_active=True)
    prix_text = "gratuitement" if instance.est_gratuit else f"pour {instance.prix} $"
    _notify_users(
        eleves,
        titre="Nouvelle ressource disponible",
        message=f"'{instance.titre}' par {instance.auteur.full_name} est disponible {prix_text}.",
        niveau=NotificationLevel.INFO,
        url=f"/marketplace/{instance.pk}/",
    )


# ============================================================
# 4. Note ajoutée → notifier l'élève
# ============================================================

@receiver(post_save, sender="students.Note")
def notify_note_added(sender, instance, created, **kwargs):
    """Quand une note est ajoutée, notifier l'élève."""
    if not created:
        return
    Notification.objects.get_or_create(
        destinataire=instance.eleve,
        titre="Nouvelle note disponible",
        message=f"Votre note pour '{instance.evaluation.titre}' est disponible : {instance.valeur}/{instance.evaluation.sur}.",
        niveau=NotificationLevel.INFO,
        url="/students/notes/",
    )
