"""
Gestionnaire personnalisé pour le modèle User.

Implémente ``create_user`` et ``create_superuser`` en cohérence
avec ``AbstractBaseUser`` et l'utilisation d'email comme identifiant.
"""
from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Manager pour le modèle User basé sur l'email.

    Méthodes publiques :
    - ``create_user(email, password, **extra_fields)``
    - ``create_superuser(email, password, **extra_fields)``
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Crée et sauvegarde un utilisateur avec l'email et le mot de passe donnés."""
        if not email:
            raise ValueError(_("L'email est obligatoire."))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Crée un utilisateur standard (is_staff=False, is_superuser=False)."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crée un superutilisateur (is_staff=True, is_superuser=True).
        Le rôle par défaut est ADMIN.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Un superutilisateur doit avoir is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Un superutilisateur doit avoir is_superuser=True."))

        return self._create_user(email, password, **extra_fields)

    # ------------------------------------------------------------
    # Méthodes utilitaires par rôle
    # ------------------------------------------------------------

    def admins(self):
        """Retourne tous les administrateurs actifs."""
        return self.filter(role="admin", is_active=True)

    def teachers(self):
        """Retourne tous les enseignants actifs."""
        return self.filter(role="enseignant", is_active=True)

    def directors(self):
        """Retourne tous les directeurs des études actifs."""
        return self.filter(role="directeur_etudes", is_active=True)

    def students(self):
        """Retourne tous les élèves actifs."""
        return self.filter(role="eleve", is_active=True)
