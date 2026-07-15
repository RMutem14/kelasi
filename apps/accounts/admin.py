"""
Configuration de l'admin Django pour le modèle User personnalisé.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from apps.accounts.enums import UserRole


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Configuration admin pour le modèle User basé sur l'email.
    Réorganise les fieldsets pour ne pas afficher le champ username.
    """

    ordering = ("last_name", "first_name", "email")
    list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("email", "first_name", "last_name", "phone")
    list_per_page = 25

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Identité"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone",
                    "avatar",
                )
            },
        ),
        (
            _("Rôle et permissions"),
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Dates importantes"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "role", "password1", "password2"),
            },
        ),
    )

    readonly_fields = ("date_joined", "last_login")

    def get_form(self, request, obj=None, **kwargs):
        """Limite les rôles proposés aux 4 rôles valides."""
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["role"].choices = UserRole.choices
        return form

    def has_delete_permission(self, request, obj=None):
        """Empêche la suppression dure de son propre compte admin."""
        if obj and obj.pk == request.user.pk:
            return False
        return super().has_delete_permission(request, obj)
