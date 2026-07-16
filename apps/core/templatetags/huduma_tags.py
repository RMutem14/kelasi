"""
Template tags personnalisés pour Huduma.

Fournit des filtres et tags utilisés par les composants du design system.
"""
from django import template

register = template.Library()


@register.filter
def get_attr(obj, key):
    """
    Récupère un attribut d'un dict ou d'un objet par clé.
    Utilisé par le composant table pour accéder aux valeurs dynamiques.

    Usage : {{ row|get_attr:col.key }}
    """
    if obj is None:
        return ""
    if isinstance(obj, dict):
        return obj.get(key, "")
    return getattr(obj, key, "")


@register.filter
def safe_html(value):
    """
    Détecte si une valeur contient du HTML à rendre tel quel.
    Utilisé par le composant table pour afficher des badges HTML dans les cellules.

    Usage : {% if cell|safe_html %}{{ cell|safe }}{% else %}{{ cell }}{% endif %}
    """
    if not isinstance(value, str):
        return False
    return value.startswith("<") and ">" in value


@register.filter
def get_item(obj, key):
    """
    Récupère une valeur dans un dict par clé.
    Utilisé pour accéder aux éléments d'un dictionnaire dans les templates.

    Usage : {{ presences_map|get_item:eleve.pk }}
    """
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


@register.simple_tag
def status_color(status_value):
    """
    Retourne la couleur Tailwind associée à un statut de document.
    Mapping défini dans apps.core.constants.STATUS_COLOR_MAP.

    Usage : {% status_color document.status as color %}
    """
    from apps.core.constants import STATUS_COLOR_MAP, DocumentStatus
    try:
        return STATUS_COLOR_MAP.get(DocumentStatus(status_value), "slate")
    except (KeyError, ValueError):
        return "slate"


@register.simple_tag
def role_badge_color(role_value):
    """
    Retourne la couleur Tailwind associée à un rôle utilisateur.
    """
    mapping = {
        "admin": "orange",
        "enseignant": "indigo",
        "directeur_etudes": "violet",
        "eleve": "sky",
    }
    return mapping.get(role_value, "slate")


@register.simple_tag
def role_label(role_value):
    """
    Retourne le libellé français d'un rôle.
    """
    mapping = {
        "admin": "Administrateur",
        "enseignant": "Enseignant",
        "directeur_etudes": "Directeur des études",
        "eleve": "Élève",
    }
    return mapping.get(role_value, role_value)
