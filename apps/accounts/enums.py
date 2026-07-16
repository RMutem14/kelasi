"""
Énumérations de l'application accounts.

Définit les quatre rôles du projet Huduma. À utiliser partout où
une notion de rôle est nécessaire (modèle User, vues, templates,
permissions, sidebars dynamiques).
"""
from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class UserRole(TextChoices):
    """
    Rôles utilisateur du projet Huduma.

    Cinq rôles:
    - ADMIN : gestion technique (utilisateurs, matières, classes, catégories)
    - ENSEIGNANT : double espace (travail pédagogique + boutique)
    - DIRECTEUR_ETUDES : validation des documents + suivi
    - ELEVE : consultation, achat, téléchargement, consultation notes
    - PARENT : suivi des enfants (notes, bulletins, absences, frais)
    """

    ADMIN = "admin", _("Administrateur")
    ENSEIGNANT = "enseignant", _("Enseignant")
    DIRECTEUR_ETUDES = "directeur_etudes", _("Directeur des études")
    ELEVE = "eleve", _("Élève")
    PARENT = "parent", _("Parent / Tuteur")


# Libellés courts pour les menus / badges
ROLE_SHORT_LABELS = {
    UserRole.ADMIN: "Admin",
    UserRole.ENSEIGNANT: "Enseignant",
    UserRole.DIRECTEUR_ETUDES: "Directeur",
    UserRole.ELEVE: "Élève",
    UserRole.PARENT: "Parent",
}

# Icônes (noms d'icônes Heroicons ou Lucide selon le design system final)
ROLE_ICONS = {
    UserRole.ADMIN: "shield-check",
    UserRole.ENSEIGNANT: "academic-cap",
    UserRole.DIRECTEUR_ETUDES: "clipboard-check",
    UserRole.ELEVE: "user-group",
    UserRole.PARENT: "users",
}
