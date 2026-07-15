"""
Context processors de l'application core.

Exposent des variables globales à tous les templates sans avoir
besoin de les passer explicitement depuis chaque vue.
"""
from django.conf import settings

from apps.accounts.enums import UserRole, ROLE_SHORT_LABELS, ROLE_ICONS
from apps.core.constants import DocumentStatus, STATUS_COLOR_MAP


def app_globals(request):
    """
    Variables globales injectées dans tous les contextes de template.

    Expose :
    - ``HUDUMA_NAME`` : nom commercial de la plateforme
    - ``HUDUMA_VERSION`` : version courte
    - ``USER_ROLES`` : rôles disponibles (liste de dicts sérialisables)
    - ``ROLE_LABELS`` : libellés courts par rôle (dict)
    - ``ROLE_ICONS`` : icônes par rôle (dict)
    - ``DOCUMENT_STATUSES`` : statuts documentaires (liste de dicts)
    - ``STATUS_COLOR_MAP`` : mapping statut -> couleur Tailwind (dict de strings)
    - ``current_user_role`` : valeur du rôle de l'utilisateur connecté
    - ``current_user_is_auth`` : booléen d'authentification
    """
    user = getattr(request, "user", None)
    is_auth = bool(user and getattr(user, "is_authenticated", False))

    # Sérialisation des enums pour éviter les erreurs de copie de contexte
    user_roles = [
        {"value": r.value, "label": r.label}
        for r in UserRole
    ]
    document_statuses = [
        {"value": s.value, "label": s.label}
        for s in DocumentStatus
    ]
    # Convertir les clés TextChoices en strings pour le mapping couleur
    status_color_map = {
        s.value: color for s, color in STATUS_COLOR_MAP.items()
    }
    # ROLE_LABELS et ROLE_ICONS utilisent déjà des clés TextChoices
    role_labels = {r.value: label for r, label in ROLE_SHORT_LABELS.items()}
    role_icons = {r.value: icon for r, icon in ROLE_ICONS.items()}

    return {
        "HUDUMA_NAME": getattr(settings, "HUDUMA_NAME", "Huduma"),
        "HUDUMA_VERSION": getattr(settings, "HUDUMA_VERSION", "0.1.0"),
        "USER_ROLES": user_roles,
        "ROLE_LABELS": role_labels,
        "ROLE_ICONS": role_icons,
        "DOCUMENT_STATUSES": document_statuses,
        "STATUS_COLOR_MAP": status_color_map,
        # Pour faciliter la sidebar dynamique
        "current_user_role": user.role if is_auth else None,
        "current_user_is_auth": is_auth,
        # Compteur de notifications non lues pour le badge navbar
        "unread_notifications_count": _get_unread_count(user) if is_auth else 0,
    }


def _get_unread_count(user):
    """Retourne le nombre de notifications non lues de l'utilisateur."""
    try:
        from apps.notifications.models import Notification
        return Notification.objects.filter(destinataire=user, lu=False).count()
    except Exception:
        return 0
