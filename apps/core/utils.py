"""
Fonctions utilitaires transverses du projet Huduma.
"""
import os


def get_env(key, default=None, cast=None):
    """
    Récupère une variable d'environnement avec un typecasting optionnel,
    tout en prenant correctement en compte le default pour chaque type.

    Args:
        key: nom de la variable d'environnement.
        default: valeur par défaut si absente.
        cast: type cible (bool, int, float, list, ou callable).

    Returns:
        La valeur castée, ou ``default`` si absente.
    """
    env_val = os.getenv(key)
    value = env_val if env_val is not None else default

    if cast is bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value

        truthy = {"1", "true", "yes", "on"}
        falsy = {"0", "false", "no", "off"}
        sval = str(value).strip().lower()

        if sval in truthy:
            return True
        if sval in falsy:
            return False
        if default is not None:
            return bool(default)
        return False

    if cast is list:
        if value is None:
            return default or []
        return [item.strip() for item in str(value).split(",") if item.strip()]

    if cast is int:
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    if cast is float:
        if value is None:
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    if callable(cast):
        try:
            return cast(value)
        except Exception:
            return default

    return value


def user_display_name(user):
    """
    Retourne le nom d'affichage d'un utilisateur.
    Privilégie le nom complet, sinon l'email, sinon 'Utilisateur'.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return "Anonyme"
    full = getattr(user, "full_name", "") or ""
    if full.strip():
        return full.strip()
    return getattr(user, "email", "Utilisateur")


def user_initials(user):
    """
    Retourne les initiales de l'utilisateur pour l'avatar.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return "?"
    first = (getattr(user, "first_name", "") or "").strip()
    last = (getattr(user, "last_name", "") or "").strip()
    if first and last:
        return f"{first[0]}{last[0]}".upper()
    if first:
        return first[0].upper()
    email = getattr(user, "email", "") or ""
    if email:
        return email[0].upper()
    return "?"

def normalize_drc_phone(phone_number: str) -> str:
    """Normalise un numéro de téléphone DRC au format +243XXXXXXXXX.

    Retourne une chaîne vide si le numéro est invalide.
    """
    if not phone_number:
        return ""

    # Ne garder que les chiffres (espaces, tirets, '+' supprimés)
    phone = ''.join(c for c in str(phone_number) if c.isdigit())

    # Supprimer le préfixe 243 s'il existe (ex: +243812345678 ou 243812345678)
    if phone.startswith('243') and len(phone) > 10:
        phone = phone[3:]

    # Supprimer le zéro initial si présent
    if phone.startswith('0'):
        phone = phone[1:]

    if len(phone) != 9 or not phone.isdigit():
        return ""

    # Ajouter le préfixe +243
    return f"+243{phone}"