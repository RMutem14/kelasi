"""
Modèle utilisateur personnalisé Huduma.

Hérite de ``AbstractBaseUser`` + ``PermissionsMixin`` (et non
``AbstractUser``) pour contourner le conflit de clé primaire entre
l'AutoField de Django et l'UUID de notre ``BaseModel``.

Identifiant principal : email (pas de username).
Clé primaire : UUID héritée de BaseModel.
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.enums import UserRole, ROLE_SHORT_LABELS
from apps.accounts.managers import UserManager
from apps.core.models.base import BaseModel


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Utilisateur Huduma.

    Champs :
    - email : identifiant unique (USERNAME_FIELD)
    - first_name / last_name : nom et prénom
    - role : un des quatre rôles (cf. UserRole)
    - is_active : compte actif
    - is_staff : accès à l'admin Django
    - phone : téléphone (optionnel)
    - avatar : image de profil (optionnel)

    Propriétés pratiques : is_admin, is_teacher, is_director, is_student,
    full_name, short_label.
    """

    email = models.EmailField(
        unique=True,
        verbose_name=_("Email"),
        help_text=_("Adresse email utilisée comme identifiant de connexion."),
    )
    first_name = models.CharField(
        max_length=80,
        verbose_name=_("Prénom"),
    )
    last_name = models.CharField(
        max_length=80,
        verbose_name=_("Nom"),
    )
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.ELEVE,
        verbose_name=_("Rôle"),
        help_text=_("Rôle de l'utilisateur dans la plateforme."),
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        default="",
        verbose_name=_("Téléphone"),
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name=_("Avatar"),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name=_("Accès admin Django"),
    )
    date_joined = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date d'inscription"),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        verbose_name = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"

    # ------------------------------------------------------------
    # Propriétés de rôle
    # ------------------------------------------------------------

    @property
    def is_admin(self) -> bool:
        """True si l'utilisateur est administrateur."""
        return self.role == UserRole.ADMIN

    @property
    def is_teacher(self) -> bool:
        """True si l'utilisateur est enseignant."""
        return self.role == UserRole.ENSEIGNANT

    @property
    def is_director(self) -> bool:
        """True si l'utilisateur est directeur des études."""
        return self.role == UserRole.DIRECTEUR_ETUDES

    @property
    def is_student(self) -> bool:
        """True si l'utilisateur est élève."""
        return self.role == UserRole.ELEVE

    # ------------------------------------------------------------
    # Propriétés d'affichage
    # ------------------------------------------------------------

    @property
    def full_name(self) -> str:
        """Nom complet (Prénom NOM)."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def short_label(self) -> str:
        """Libellé court du rôle, pour menus et badges."""
        return ROLE_SHORT_LABELS.get(self.role, self.role)

    @property
    def initials(self) -> str:
        """Initiales pour l'avatar (2 lettres majuscules)."""
        first = (self.first_name or "").strip()
        last = (self.last_name or "").strip()
        if first and last:
            return f"{first[0]}{last[0]}".upper()
        if first:
            return first[0].upper()
        if self.email:
            return self.email[0].upper()
        return "?"
