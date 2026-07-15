"""
Vues du tableau de bord et pages diverses.

- DashboardHomeView : redirige vers le dashboard du rôle
- DesignSystemView : page de démonstration du design system
- RolesView : page de gestion des rôles & accès (admin)
- LandingPageView : page d'accueil publique (avant login)
"""
from django.shortcuts import redirect
from django.views.generic import TemplateView

from apps.accounts.enums import UserRole, ROLE_SHORT_LABELS, ROLE_ICONS
from apps.core.constants import DocumentStatus, STATUS_COLOR_MAP


# ------------------------------------------------------------
# Mapping rôle -> template
# ------------------------------------------------------------

ROLE_DASHBOARD_TEMPLATES = {
    UserRole.ADMIN: "pages/dashboard/admin.html",
    UserRole.ENSEIGNANT: "pages/dashboard/enseignant.html",
    UserRole.DIRECTEUR_ETUDES: "pages/dashboard/directeur.html",
    UserRole.ELEVE: "pages/dashboard/eleve.html",
}


class ProfileView(TemplateView):
    """Page de profil de l'utilisateur connecté."""
    template_name = "pages/dashboard/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["page_title"] = "Mon profil"
        context["page_subtitle"] = "Vos informations personnelles et activité."
        # Stats selon le rôle
        if user.role == UserRole.ENSEIGNANT:
            from apps.pedagogy.models import DocumentPedagogique
            from apps.marketplace.models import Resource, Order
            from apps.core.constants import DocumentStatus, PublicationStatus
            context["user_stats"] = {
                "documents": DocumentPedagogique.objects.filter(auteur=user).count(),
                "documents_valides": DocumentPedagogique.objects.filter(auteur=user, statut=DocumentStatus.VALIDE).count(),
                "ressources": Resource.objects.filter(auteur=user).count(),
                "ventes": Order.objects.filter(ressource__auteur=user).count(),
            }
        elif user.role == UserRole.ELEVE:
            from apps.students.models import Note, ResourceAccess
            context["user_stats"] = {
                "notes": Note.objects.filter(eleve=user).count(),
                "ressources": ResourceAccess.objects.filter(eleve=user).count(),
            }
        elif user.role == UserRole.ADMIN:
            from apps.accounts.models import User
            context["user_stats"] = {
                "utilisateurs": User.objects.count(),
            }
        elif user.role == UserRole.DIRECTEUR_ETUDES:
            from apps.pedagogy.models import DocumentPedagogique
            from apps.core.constants import DocumentStatus
            context["user_stats"] = {
                "a_valider": DocumentPedagogique.objects.filter(statut=DocumentStatus.SOUMIS).count(),
                "valides": DocumentPedagogique.objects.filter(statut=DocumentStatus.VALIDE).count(),
            }
        return context


class SettingsView(TemplateView):
    """Page de paramètres (admin uniquement)."""
    template_name = "pages/admin/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Paramètres"
        context["page_subtitle"] = "Configuration générale de la plateforme."
        return context


class DirecteurStatsView(TemplateView):
    """Page de statistiques pour le directeur des études."""
    template_name = "pages/directeur/stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Statistiques"
        context["page_subtitle"] = "Vue d'ensemble de l'activité pédagogique."
        from apps.pedagogy.models import DocumentPedagogique
        from apps.academic.models import Classe, Cours
        from apps.core.constants import DocumentStatus
        from apps.accounts.models import User
        from apps.accounts.enums import UserRole
        context["stats"] = {
            "documents_total": DocumentPedagogique.objects.count(),
            "documents_valides": DocumentPedagogique.objects.filter(statut=DocumentStatus.VALIDE).count(),
            "documents_en_attente": DocumentPedagogique.objects.filter(statut=DocumentStatus.SOUMIS).count(),
            "documents_corrections": DocumentPedagogique.objects.filter(statut=DocumentStatus.CORRECTION).count(),
            "classes": Classe.objects.count(),
            "cours": Cours.objects.count(),
            "enseignants": User.objects.filter(role=UserRole.ENSEIGNANT, is_active=True).count(),
        }
        # Documents par type
        context["docs_par_type"] = []
        for type_val, type_label in DocumentPedagogique.Type.choices:
            count = DocumentPedagogique.objects.filter(type=type_val).count()
            context["docs_par_type"].append({"label": type_label, "count": count})
        # Documents par enseignant
        from django.db.models import Count
        context["docs_par_enseignant"] = (
            DocumentPedagogique.objects.values("auteur__first_name", "auteur__last_name")
            .annotate(total=Count("id"))
            .order_by("-total")[:5]
        )
        return context


class LandingPageView(TemplateView):
    """Page d'accueil publique (landing page) accessible sans login."""

    template_name = "pages/landing.html"


class DashboardHomeView(TemplateView):
    """Vue racine du dashboard : redirige vers le dashboard du rôle."""

    template_name = "pages/dashboard/home.html"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect("accounts:login")

        context = self.get_context_data()
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["page_title"] = f"Tableau de bord — {user.short_label}"
        context["page_subtitle"] = self._get_role_subtitle(user.role)
        context["stats_cards"] = self._get_fake_stats(user.role)
        context["recent_users"] = self._get_fake_recent_users()

        # Données pour le dashboard admin (tableau comptes récents)
        if user.role == UserRole.ADMIN:
            context["columns"] = [
                {"key": "user", "label": "Utilisateur", "align": "left"},
                {"key": "role", "label": "Rôle", "align": "left"},
                {"key": "classe", "label": "Classe", "align": "left"},
                {"key": "status", "label": "Statut", "align": "left"},
            ]
            context["table_actions"] = [
                {"icon": "eye", "color": "indigo", "url": "#", "label": "Voir"},
                {"icon": "edit-3", "color": "slate", "url": "#", "label": "Modifier"},
                {"icon": "trash-2", "color": "red", "url": "#", "label": "Supprimer"},
            ]
        return context

    def get_template_names(self):
        user = self.request.user
        template = ROLE_DASHBOARD_TEMPLATES.get(user.role, self.template_name)
        return [template]

    def _get_role_subtitle(self, role):
        subtitles = {
            UserRole.ADMIN: "Gérez les comptes, les classes, les contenus et les accès de la plateforme.",
            UserRole.ENSEIGNANT: "Votre travail pédagogique et votre boutique.",
            UserRole.DIRECTEUR_ETUDES: "Consultez les classes et les cours, validez les documents pédagogiques.",
            UserRole.ELEVE: "Vos ressources, achats et notes.",
        }
        return subtitles.get(role, "Bienvenue sur votre espace.")

    def _get_fake_stats(self, role):
        if role == UserRole.ADMIN:
            return [
                {"label": "Utilisateurs", "value": 24, "icon": "users", "color": "indigo",
                 "badge": "Admin", "footer": "Comptes actuellement enregistrés"},
                {"label": "Classes", "value": 6, "icon": "school", "color": "emerald",
                 "badge": "Actives", "footer": "Classes configurées dans le système"},
                {"label": "Documents", "value": 18, "icon": "folder-open", "color": "sky",
                 "badge": "Publié", "footer": "Supports pédagogiques disponibles"},
                {"label": "Rôles", "value": 4, "icon": "shield-check", "color": "orange",
                 "badge": "Accès", "footer": "Admin, enseignant, élève, direction"},
            ]
        if role == UserRole.ENSEIGNANT:
            return [
                {"label": "Brouillons", "value": 3, "icon": "file-edit", "color": "amber",
                 "footer": "Documents en cours de rédaction"},
                {"label": "Soumis", "value": 2, "icon": "send", "color": "sky",
                 "footer": "En attente de validation"},
                {"label": "Validés", "value": 14, "icon": "check-circle", "color": "emerald",
                 "footer": "Documents validés ce mois"},
                {"label": "Ressources publiées", "value": 5, "icon": "book-marked", "color": "indigo",
                 "footer": "Dans la bibliothèque"},
            ]
        if role == UserRole.DIRECTEUR_ETUDES:
            return [
                {"label": "Documents en attente", "value": 5, "icon": "clock", "color": "amber"},
                {"label": "Documents à corriger", "value": 2, "icon": "rotate-ccw", "color": "red"},
                {"label": "Classes consultables", "value": 6, "icon": "school", "color": "indigo"},
                {"label": "Cours consultables", "value": 12, "icon": "book-open", "color": "violet"},
            ]
        if role == UserRole.ELEVE:
            return [
                {"label": "Mes ressources", "value": 8, "icon": "book", "color": "indigo",
                 "footer": "Ressources accessibles"},
                {"label": "Ressources achetées", "value": 3, "icon": "shopping-bag", "color": "emerald",
                 "footer": "Achats effectués"},
                {"label": "Notes récentes", "value": 5, "icon": "clipboard-list", "color": "sky",
                 "footer": "Dernières évaluations"},
                {"label": "À télécharger", "value": 2, "icon": "download", "color": "amber",
                 "footer": "Nouveaux contenus disponibles"},
            ]
        return []

    def _get_fake_recent_users(self):
        return [
            {
                "user": '<div class="flex items-center gap-3"><div class="w-10 h-10 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold">A</div><div><p class="font-bold text-slate-900">Madame Amani</p><p class="text-slate-400 text-xs">amani@elikya.cd</p></div></div>',
                "role": "Enseignante",
                "classe": "5ème A",
                "status": '<span class="px-3 py-1 rounded-full bg-emerald-50 text-emerald-600 font-semibold text-xs">Actif</span>',
            },
            {
                "user": '<div class="flex items-center gap-3"><div class="w-10 h-10 rounded-full bg-sky-100 text-sky-600 flex items-center justify-center font-bold">J</div><div><p class="font-bold text-slate-900">Jean Kalala</p><p class="text-slate-400 text-xs">jean.kalala@elikya.cd</p></div></div>',
                "role": "Élève",
                "classe": "6ème A",
                "status": '<span class="px-3 py-1 rounded-full bg-emerald-50 text-emerald-600 font-semibold text-xs">Actif</span>',
            },
            {
                "user": '<div class="flex items-center gap-3"><div class="w-10 h-10 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center font-bold">D</div><div><p class="font-bold text-slate-900">Direction Études</p><p class="text-slate-400 text-xs">direction@elikya.cd</p></div></div>',
                "role": "Direction",
                "classe": "Toutes",
                "status": '<span class="px-3 py-1 rounded-full bg-amber-50 text-amber-600 font-semibold text-xs">À vérifier</span>',
            },
        ]


class DesignSystemView(TemplateView):
    """Page de démonstration du design system."""

    template_name = "pages/dashboard/design_system.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Design System"
        context["page_subtitle"] = "Catalogue des composants réutilisables"

        context["demo_columns"] = [
            {"key": "user", "label": "Utilisateur", "align": "left"},
            {"key": "role", "label": "Rôle", "align": "left"},
            {"key": "class", "label": "Classe", "align": "left"},
            {"key": "status", "label": "Statut", "align": "left"},
        ]
        context["demo_rows"] = [
            {"user": "<b>Madame Amani</b>", "role": "Enseignante", "class": "5ème A", "status": "actif"},
            {"user": "<b>Jean Kalala</b>", "role": "Élève", "class": "6ème A", "status": "valide"},
            {"user": "<b>Direction</b>", "role": "Directeur", "class": "Toutes", "status": "en_attente"},
        ]
        context["demo_actions"] = [
            {"icon": "eye", "color": "indigo", "url": "#", "label": "Voir"},
            {"icon": "edit-3", "color": "slate", "url": "#", "label": "Modifier"},
            {"icon": "trash-2", "color": "red", "url": "#", "label": "Supprimer"},
        ]
        context["demo_role_options"] = [
            {"value": "enseignant", "label": "Enseignant"},
            {"value": "eleve", "label": "Élève"},
            {"value": "directeur_etudes", "label": "Directeur des études"},
        ]
        context["demo_sexe_options"] = [
            {"value": "f", "label": "Féminin"},
            {"value": "m", "label": "Masculin"},
        ]
        context["breadcrumb_items"] = [
            {"label": "Accueil", "url": "/"},
            {"label": "Design System"},
        ]
        context["dropdown_items"] = [
            {"label": "Voir détails", "icon": "eye", "url": "#"},
            {"label": "Modifier", "icon": "edit-3", "url": "#"},
            {"divider": True},
            {"label": "Supprimer", "icon": "trash-2", "url": "#", "danger": True},
        ]
        return context


class RolesView(TemplateView):
    """Page de gestion des rôles & accès (admin)."""

    template_name = "pages/admin/roles/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Rôles & accès"
        context["page_subtitle"] = "Définissez les niveaux d'autorisation et contrôlez les accès aux modules."
        # Données des rôles pour l'affichage
        context["roles_data"] = [
            {
                "value": UserRole.ADMIN,
                "label": "Administrateur",
                "icon": "shield-check",
                "color": "orange",
                "description": "Accès complet à la plateforme : utilisateurs, classes, cours, documents, évaluations, rôles.",
                "permissions": ["Créer/Modifier/Supprimer utilisateurs", "Gérer classes & cours", "Gérer rôles & accès", "Accès admin Django"],
                "user_count": self._count_users(UserRole.ADMIN),
            },
            {
                "value": UserRole.ENSEIGNANT,
                "label": "Enseignant",
                "icon": "academic-cap",
                "color": "indigo",
                "description": "Double espace : travail pédagogique (documents à valider) + boutique (ressources commercialisables).",
                "permissions": ["Créer documents pédagogiques", "Soumettre au directeur", "Publier ressources", "Voir ses ventes"],
                "user_count": self._count_users(UserRole.ENSEIGNANT),
            },
            {
                "value": UserRole.DIRECTEUR_ETUDES,
                "label": "Directeur des études",
                "icon": "clipboard-check",
                "color": "violet",
                "description": "Validation des documents pédagogiques et suivi des enseignants. Pas d'accès à la marketplace.",
                "permissions": ["Valider/rejeter documents", "Demander corrections", "Consulter classes & cours", "Suivi enseignants"],
                "user_count": self._count_users(UserRole.DIRECTEUR_ETUDES),
            },
            {
                "value": UserRole.ELEVE,
                "label": "Élève",
                "icon": "user-group",
                "color": "sky",
                "description": "Consultation des ressources gratuites, achat de ressources, téléchargement, consultation des notes.",
                "permissions": ["Consulter ressources", "Acheter ressources", "Télécharger", "Voir ses notes"],
                "user_count": self._count_users(UserRole.ELEVE),
            },
        ]
        return context

    def _count_users(self, role):
        from apps.accounts.models import User
        return User.objects.filter(role=role, is_active=True).count()
