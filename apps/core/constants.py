"""
Constantes globales du projet Huduma.

Centralise toutes les énumérations (TextChoices) utilisées par les
modèles métier afin d'éviter les chaînes de caractères en dur et
les duplications d'énumérations par module.

Convention : un seul DocumentStatus pour TOUS les documents pédagogiques
(jamais PreparationStatus, JournalStatus, etc.).
"""
from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class DocumentStatus(TextChoices):
    """Statuts du workflow pédagogique (validation Directeur des études)."""

    BROUILLON = "brouillon", _("Brouillon")
    SOUMIS = "soumis", _("Soumis")
    CORRECTION = "correction", _("Correction demandée")
    VALIDE = "valide", _("Validé")
    REJETE = "rejete", _("Rejeté")


class PublicationStatus(TextChoices):
    """Statuts du workflow commercial (marketplace)."""

    BROUILLON = "brouillon", _("Brouillon")
    PUBLIE = "publie", _("Publié")
    ARCHIVE = "archive", _("Archivé")
    RETIRE = "retire", _("Retiré")


class OrderStatus(TextChoices):
    """Statuts d'une commande dans la marketplace."""

    EN_ATTENTE = "en_attente", _("En attente de paiement")
    PAYE = "paye", _("Payé")
    ECHOUE = "echoue", _("Échec du paiement")
    REMBOURSE = "rembourse", _("Remboursé")


class ResourceType(TextChoices):
    """Types de ressources commercialisables dans la bibliothèque."""

    SYLLABUS = "syllabus", _("Syllabus")
    SUPPORT = "support", _("Support de cours")
    EXERCICE = "exercice", _("Exercice")
    TP = "tp", _("Travail pratique")
    EXAMEN = "examen", _("Examen")
    LIVRE = "livre", _("Livre numérique")
    CORRIGE = "corrige", _("Corrigé")


class ResourceCategory(TextChoices):
    """Catégories pédagogiques transverses pour organiser le catalogue."""

    COURS = "cours", _("Cours")
    EXERCICE = "exercice", _("Exercices")
    EVALUATION = "evaluation", _("Évaluation")
    REFERENCE = "reference", _("Référence")
    METHODOLOGIE = "methodologie", _("Méthodologie")


class NotificationLevel(TextChoices):
    """Niveaux de sévérité des notifications internes."""

    INFO = "info", _("Information")
    SUCCESS = "success", _("Succès")
    WARNING = "warning", _("Avertissement")
    ERROR = "error", _("Erreur")


# ------------------------------------------------------------
# Mappings de présentation
# ------------------------------------------------------------

# Mapping statut de document -> classe de couleur Tailwind
# (utilisé par templates/components/feedback/status_badge.html)
STATUS_COLOR_MAP = {
    DocumentStatus.BROUILLON: "amber",
    DocumentStatus.SOUMIS: "sky",
    DocumentStatus.CORRECTION: "amber",
    DocumentStatus.VALIDE: "emerald",
    DocumentStatus.REJETE: "red",
}

# Mapping niveau de notification -> classe de couleur Tailwind
NOTIFICATION_COLOR_MAP = {
    NotificationLevel.INFO: "sky",
    NotificationLevel.SUCCESS: "emerald",
    NotificationLevel.WARNING: "amber",
    NotificationLevel.ERROR: "red",
}


def get_status_color(status):
    """Retourne la couleur Tailwind associée à un statut de document."""
    return STATUS_COLOR_MAP.get(status, "slate")
