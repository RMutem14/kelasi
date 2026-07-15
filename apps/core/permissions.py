"""
Permissions par rôle du projet Huduma.

Centralise les vérifications de permissions métier (par opposition aux
permissions Django standards qui sont génériques). À utiliser dans les
vues, mixins, templates et signatures de signal.

Convention : fonctions ``can_*`` qui prennent un utilisateur en paramètre
et retournent un booléen. Le paramètre ``obj`` est optionnel pour les
vérifications de propriété.
"""
from django.contrib.auth.models import AnonymousUser

from apps.accounts.enums import UserRole


def _is_role(user, role) -> bool:
    """Vérifie si l'utilisateur a le rôle donné. Tolérant aux AnonymousUser."""
    if user is None or isinstance(user, AnonymousUser):
        return False
    if not getattr(user, "is_authenticated", False):
        return False
    return user.role == role


# ------------------------------------------------------------
# Permissions sur les documents pédagogiques
# ------------------------------------------------------------

def can_create_document(user) -> bool:
    """Seuls les enseignants et le directeur peuvent créer des documents."""
    return _is_role(user, UserRole.ENSEIGNANT) or _is_role(user, UserRole.DIRECTEUR_ETUDES)


def can_edit_document(user, document=None) -> bool:
    """
    L'enseignant propriétaire peut modifier son document, tant qu'il
    n'est pas validé. Le directeur peut modifier tous les documents.
    """
    if not _is_role(user, UserRole.ENSEIGNANT) and not _is_role(user, UserRole.DIRECTEUR_ETUDES):
        return False
    if document is None:
        return True
    if _is_role(user, UserRole.DIRECTEUR_ETUDES):
        return True
    owner = getattr(document, "created_by", None)
    return owner == user


def can_submit_document(user, document=None) -> bool:
    """L'enseignant propriétaire peut soumettre son document."""
    if not _is_role(user, UserRole.ENSEIGNANT):
        return False
    if document is None:
        return True
    return getattr(document, "created_by", None) == user


def can_validate_document(user) -> bool:
    """Seul le directeur des études peut valider/rejeter un document."""
    return _is_role(user, UserRole.DIRECTEUR_ETUDES)


# ------------------------------------------------------------
# Permissions sur la marketplace
# ------------------------------------------------------------

def can_publish_resource(user) -> bool:
    """Seuls les enseignants peuvent publier des ressources."""
    return _is_role(user, UserRole.ENSEIGNANT)


def can_buy_resource(user) -> bool:
    """Seuls les élèves peuvent acheter des ressources."""
    return _is_role(user, UserRole.ELEVE)


def can_download_resource(user, resource=None, purchase=None) -> bool:
    """
    Un élève peut télécharger une ressource gratuite ou qu'il a achetée.
    L'enseignant propriétaire peut télécharger sa propre ressource.
    """
    if _is_role(user, UserRole.ENSEIGNANT):
        if resource is None:
            return True
        return getattr(resource, "created_by", None) == user
    if _is_role(user, UserRole.ELEVE):
        if resource is None:
            return True
        # Gratuit : tout élève peut télécharger
        price = getattr(resource, "price", 0) or 0
        if price == 0:
            return True
        # Payant : vérifie l'achat
        if purchase is None:
            return False
        return getattr(purchase, "user", None) == user
    return False


# ------------------------------------------------------------
# Permissions d'administration
# ------------------------------------------------------------

def can_manage_users(user) -> bool:
    """Seul l'admin peut gérer les utilisateurs."""
    return _is_role(user, UserRole.ADMIN)


def can_manage_academic(user) -> bool:
    """Admin et directeur peuvent configurer l'académique (classes, matières)."""
    return _is_role(user, UserRole.ADMIN) or _is_role(user, UserRole.DIRECTEUR_ETUDES)


def can_view_dashboard_for_role(user, target_role) -> bool:
    """Vérifie si un utilisateur peut voir le dashboard d'un rôle donné."""
    if not getattr(user, "is_authenticated", False):
        return False
    return user.role == target_role or _is_role(user, UserRole.ADMIN)
