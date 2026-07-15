"""
Vues de gestion des utilisateurs (admin) et authentification.

CRUD complet avec HTMX :
- Liste avec recherche et filtres
- Détail via modal HTMX
- Ajout / édition / suppression

Vues d'auth :
- LoginView : connexion par email + mot de passe
- logout_view : déconnexion et redirection
"""
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.accounts.enums import UserRole
from apps.accounts.models import User
from apps.core.mixins import RoleRequiredMixin


# ============================================================
# AUTHENTIFICATION
# ============================================================

class LoginView(DjangoLoginView):
    """Vue de connexion personnalisée basée sur l'email."""

    template_name = "pages/accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        next_url = self.get_redirect_url()
        if next_url:
            return next_url
        return reverse_lazy("dashboard:home")


def logout_view(request):
    """Vue de déconnexion : termine la session et redirige vers login."""
    auth_logout(request)
    return redirect(reverse_lazy("accounts:login"))


# ============================================================
# GESTION DES UTILISATEURS (ADMIN)
# ============================================================


class UserListView(RoleRequiredMixin, ListView):
    """Liste des utilisateurs avec filtres par rôle."""
    model = User
    template_name = "pages/admin/users/index.html"
    context_object_name = "users"
    paginate_by = 10
    allowed_roles = [UserRole.ADMIN]

    def get_queryset(self):
        qs = User.objects.select_related("created_by").all().order_by("-date_joined")
        role_filter = self.request.GET.get("role", "")
        search = self.request.GET.get("search", "").strip()
        if role_filter:
            qs = qs.filter(role=role_filter)
        if search:
            qs = qs.filter(
                models_Q_first_name_or_last_name_or_email(search)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Gestion des utilisateurs"
        ctx["page_subtitle"] = "Ajoutez, contrôlez et organisez les comptes selon leurs rôles."
        ctx["active_role_filter"] = self.request.GET.get("role", "")
        ctx["search_query"] = self.request.GET.get("search", "")
        ctx["role_choices"] = UserRole.choices
        # Stats pour les cartes
        ctx["stats"] = {
            "total": User.objects.count(),
            "enseignants": User.objects.filter(role=UserRole.ENSEIGNANT).count(),
            "eleves": User.objects.filter(role=UserRole.ELEVE).count(),
            "directeurs": User.objects.filter(role=UserRole.DIRECTEUR_ETUDES).count(),
        }
        return ctx


def models_Q_first_name_or_last_name_or_email(search):
    """Helper pour construire le Q de recherche."""
    from django.db.models import Q
    return Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(email__icontains=search)


class UserDetailView(RoleRequiredMixin, View):
    """Détail d'un utilisateur via modal HTMX."""
    allowed_roles = [UserRole.ADMIN]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return render(request, "pages/admin/users/_detail_modal.html", {"user": user})


class UserCreateView(RoleRequiredMixin, View):
    """Création d'un utilisateur."""
    allowed_roles = [UserRole.ADMIN]
    template_name = "pages/admin/users/ajouter.html"

    def get(self, request):
        ctx = {
            "page_title": "Ajouter un utilisateur",
            "page_subtitle": "Créez un compte et renseignez les informations selon le rôle choisi.",
            "role_choices": UserRole.choices,
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        password = request.POST.get("password", "").strip()
        role = request.POST.get("role", UserRole.ELEVE)
        phone = request.POST.get("phone", "").strip()

        if not email or not first_name or not last_name or not password:
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
            return redirect("accounts:user_add")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Un compte avec cet email existe déjà.")
            return redirect("accounts:user_add")

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            phone=phone,
        )
        messages.success(request, f"Utilisateur {user.full_name} créé avec succès.")
        return redirect("accounts:user_list")


class UserDeleteView(RoleRequiredMixin, View):
    """Suppression (soft delete) d'un utilisateur."""
    allowed_roles = [UserRole.ADMIN]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user.pk == request.user.pk:
            messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
            return redirect("accounts:user_list")
        name = user.full_name
        user.soft_delete(user=request.user)
        messages.success(request, f"Utilisateur {name} supprimé.")
        return redirect("accounts:user_list")



class UserEditView(RoleRequiredMixin, View):
    """Édition d'un utilisateur."""
    allowed_roles = [UserRole.ADMIN]
    template_name = "pages/admin/users/ajouter.html"

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        ctx = {
            "page_title": "Modifier l'utilisateur",
            "page_subtitle": f"Édition de '{user.full_name}'",
            "edit_user": user,
            "role_choices": UserRole.choices,
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.first_name = request.POST.get("first_name", user.first_name).strip()
        user.last_name = request.POST.get("last_name", user.last_name).strip()
        user.role = request.POST.get("role", user.role)
        user.phone = request.POST.get("phone", "").strip()
        new_password = request.POST.get("password", "").strip()
        if new_password:
            user.set_password(new_password)
        user.updated_by = request.user
        user.save()
        messages.success(request, f"Utilisateur '{user.full_name}' modifié.")
        return redirect("accounts:user_list")
