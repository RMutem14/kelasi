"""
Vues de gestion académique (admin).

CRUD pour les classes, cours et évaluations.
"""
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from apps.accounts.enums import UserRole
from apps.academic.models import Classe, Cours, Evaluation
from apps.core.mixins import RoleRequiredMixin


# ============================================================
# CLASSES
# ============================================================

class ClasseListView(RoleRequiredMixin, ListView):
    """Liste des classes."""
    model = Classe
    template_name = "pages/admin/classes/index.html"
    context_object_name = "classes"
    allowed_roles = [UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]

    def get_queryset(self):
        qs = Classe.objects.select_related("titulaire", "annee_scolaire").all().order_by("nom")
        statut = self.request.GET.get("statut", "")
        if statut:
            qs = qs.filter(statut=statut)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Gestion des classes"
        ctx["page_subtitle"] = "Créez, organisez et suivez les classes disponibles."
        ctx["active_statut"] = self.request.GET.get("statut", "")
        ctx["stats"] = {
            "total": Classe.objects.count(),
            "actives": Classe.objects.filter(statut=Classe.Statut.ACTIVE).count(),
            "suspendues": Classe.objects.filter(statut=Classe.Statut.SUSPENDUE).count(),
            "sans_titulaire": Classe.objects.filter(titulaire__isnull=True).count(),
        }
        return ctx


class ClasseDetailView(RoleRequiredMixin, View):
    """Détail d'une classe via modal HTMX."""
    allowed_roles = [UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]

    def get(self, request, pk):
        classe = get_object_or_404(Classe.objects.select_related("titulaire", "annee_scolaire"), pk=pk)
        cours_list = classe.cours.select_related("enseignant").all()
        return render(request, "pages/admin/classes/_detail_modal.html", {
            "classe": classe,
            "cours_list": cours_list,
        })


class ClasseCreateView(RoleRequiredMixin, View):
    """Création d'une classe."""
    allowed_roles = [UserRole.ADMIN]
    template_name = "pages/admin/classes/ajouter.html"

    def get(self, request):
        from apps.academic.models import AnneeScolaire
        enseignants = UserRole  # pour le template
        ctx = {
            "page_title": "Ajouter une classe",
            "page_subtitle": "Créez une nouvelle classe et associez un titulaire.",
            "enseignants": __import__("apps.accounts.models", fromlist=["User"]).User.objects.filter(
                role=UserRole.ENSEIGNANT, is_active=True
            ),
            "annees": AnneeScolaire.objects.all(),
            "niveau_choices": Classe.Niveau.choices,
            "statut_choices": Classe.Statut.choices,
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        nom = request.POST.get("nom", "").strip()
        niveau = request.POST.get("niveau", Classe.Niveau.SECONDAIRE)
        section = request.POST.get("section", "").strip()
        titulaire_id = request.POST.get("titulaire", "")
        effectif = request.POST.get("effectif", 0)
        statut = request.POST.get("statut", Classe.Statut.ACTIVE)

        if not nom:
            messages.error(request, "Le nom de la classe est obligatoire.")
            return redirect("academic:classe_add")

        from apps.accounts.models import User
        titulaire = User.objects.filter(pk=titulaire_id).first() if titulaire_id else None

        Classe.objects.create(
            nom=nom, niveau=niveau, section=section,
            titulaire=titulaire, effectif=int(effectif), statut=statut,
            created_by=request.user,
        )
        messages.success(request, f"Classe {nom} créée avec succès.")
        return redirect("academic:classe_list")


# ============================================================
# COURS
# ============================================================

class CoursListView(RoleRequiredMixin, ListView):
    """Liste des cours."""
    model = Cours
    template_name = "pages/admin/cours/index.html"
    context_object_name = "cours_list"
    allowed_roles = [UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]

    def get_queryset(self):
        qs = Cours.objects.select_related("classe", "enseignant").all().order_by("classe__nom", "nom")
        statut = self.request.GET.get("statut", "")
        if statut:
            qs = qs.filter(statut=statut)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Gestion des cours"
        ctx["page_subtitle"] = "Organisez les matières, les enseignants et les classes associées."
        ctx["active_statut"] = self.request.GET.get("statut", "")
        ctx["stats"] = {
            "total": Cours.objects.count(),
            "enseignants": Cours.objects.filter(enseignant__isnull=False).values("enseignant").distinct().count(),
            "classes": Cours.objects.values("classe").distinct().count(),
            "sans_enseignant": Cours.objects.filter(enseignant__isnull=True).count(),
        }
        return ctx


class CoursDetailView(RoleRequiredMixin, View):
    """Détail d'un cours via modal HTMX."""
    allowed_roles = [UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]

    def get(self, request, pk):
        cours = get_object_or_404(Cours.objects.select_related("classe", "enseignant"), pk=pk)
        return render(request, "pages/admin/cours/_detail_modal.html", {"cours": cours})


class CoursCreateView(RoleRequiredMixin, View):
    """Création d'un cours."""
    allowed_roles = [UserRole.ADMIN]
    template_name = "pages/admin/cours/ajouter.html"

    def get(self, request):
        from apps.accounts.models import User
        ctx = {
            "page_title": "Ajouter un cours",
            "page_subtitle": "Créez un cours et associez-le à une classe et un enseignant.",
            "classes": Classe.objects.all(),
            "enseignants": User.objects.filter(role=UserRole.ENSEIGNANT, is_active=True),
            "statut_choices": Cours.Statut.choices,
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        nom = request.POST.get("nom", "").strip()
        code = request.POST.get("code", "").strip()
        classe_id = request.POST.get("classe", "")
        enseignant_id = request.POST.get("enseignant", "")
        coefficient = request.POST.get("coefficient", 1)
        description = request.POST.get("description", "").strip()

        if not nom or not code or not classe_id:
            messages.error(request, "Nom, code et classe sont obligatoires.")
            return redirect("academic:cours_add")

        from apps.accounts.models import User
        classe = get_object_or_404(Classe, pk=classe_id)
        enseignant = User.objects.filter(pk=enseignant_id).first() if enseignant_id else None

        Cours.objects.create(
            nom=nom, code=code, classe=classe, enseignant=enseignant,
            coefficient=int(coefficient), description=description,
            statut=Cours.Statut.ACTIF if enseignant else Cours.Statut.SANS_ENSEIGNANT,
            created_by=request.user,
        )
        messages.success(request, f"Cours {nom} créé avec succès.")
        return redirect("academic:cours_list")


# ============================================================
# ÉVALUATIONS
# ============================================================

class EvaluationListView(RoleRequiredMixin, ListView):
    """Liste des évaluations."""
    model = Evaluation
    template_name = "pages/admin/evaluation/index.html"
    context_object_name = "evaluations"
    allowed_roles = [UserRole.ADMIN, UserRole.ENSEIGNANT]

    def get_queryset(self):
        user = self.request.user
        qs = Evaluation.objects.select_related("classe", "cours", "enseignant").all().order_by("-date_evaluation")
        if user.role == UserRole.ENSEIGNANT:
            qs = qs.filter(enseignant=user)
        statut = self.request.GET.get("statut", "")
        if statut:
            qs = qs.filter(statut=statut)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Gestion des évaluations"
        ctx["page_subtitle"] = "Créez des devoirs, interrogations et examens."
        ctx["active_statut"] = self.request.GET.get("statut", "")
        ctx["stats"] = {
            "total": Evaluation.objects.count(),
            "programmees": Evaluation.objects.filter(statut=Evaluation.Statut.PROGRAMMEE).count(),
            "terminees": Evaluation.objects.filter(statut=Evaluation.Statut.TERMINEE).count(),
            "corrigees": Evaluation.objects.filter(statut=Evaluation.Statut.CORRIGEE).count(),
        }
        return ctx


class EvaluationCreateView(RoleRequiredMixin, View):
    """Création d'une évaluation."""
    allowed_roles = [UserRole.ADMIN, UserRole.ENSEIGNANT]
    template_name = "pages/admin/evaluation/ajouter.html"

    def get(self, request):
        from apps.accounts.models import User
        ctx = {
            "page_title": "Ajouter une évaluation",
            "page_subtitle": "Créez un devoir, interrogation ou examen.",
            "classes": Classe.objects.all(),
            "cours_list": Cours.objects.select_related("classe").all(),
            "enseignants": User.objects.filter(role=UserRole.ENSEIGNANT, is_active=True),
            "type_choices": Evaluation.Type.choices,
            "statut_choices": Evaluation.Statut.choices,
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        titre = request.POST.get("titre", "").strip()
        type_eval = request.POST.get("type", Evaluation.Type.DEVOIR)
        classe_id = request.POST.get("classe", "")
        cours_id = request.POST.get("cours", "")
        enseignant_id = request.POST.get("enseignant", "")
        date_eval = request.POST.get("date_evaluation", "")
        duree = request.POST.get("duree_minutes", 60)
        sur = request.POST.get("sur", 20)
        description = request.POST.get("description", "").strip()

        if not titre or not classe_id or not cours_id:
            messages.error(request, "Titre, classe et cours sont obligatoires.")
            return redirect("academic:evaluation_add")

        from apps.accounts.models import User
        classe = get_object_or_404(Classe, pk=classe_id)
        cours = get_object_or_404(Cours, pk=cours_id)
        enseignant = User.objects.filter(pk=enseignant_id).first() if enseignant_id else request.user

        from datetime import datetime
        date_obj = None
        if date_eval:
            try:
                date_obj = datetime.strptime(date_eval, "%Y-%m-%d").date()
            except ValueError:
                pass

        Evaluation.objects.create(
            titre=titre, type=type_eval, classe=classe, cours=cours,
            enseignant=enseignant, date_evaluation=date_obj,
            duree_minutes=int(duree), sur=int(sur), description=description,
            created_by=request.user,
        )
        messages.success(request, f"Évaluation {titre} créée avec succès.")
        return redirect("academic:evaluation_list")


# ============================================================
# ÉDITION ET SUPPRESSION
# ============================================================

class ClasseEditView(RoleRequiredMixin, View):
    """Édition d'une classe."""
    allowed_roles = [UserRole.ADMIN]
    template_name = "pages/admin/classes/ajouter.html"

    def get(self, request, pk):
        classe = get_object_or_404(Classe, pk=pk)
        from apps.accounts.models import User
        from apps.academic.models import AnneeScolaire
        ctx = {
            "page_title": "Modifier la classe",
            "page_subtitle": f"Édition de '{classe.nom}'",
            "classe": classe,
            "enseignants": User.objects.filter(role=UserRole.ENSEIGNANT, is_active=True),
            "annees": AnneeScolaire.objects.all(),
            "niveau_choices": Classe.Niveau.choices,
            "statut_choices": Classe.Statut.choices,
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk):
        classe = get_object_or_404(Classe, pk=pk)
        classe.nom = request.POST.get("nom", classe.nom).strip()
        classe.niveau = request.POST.get("niveau", classe.niveau)
        classe.section = request.POST.get("section", "").strip()
        titulaire_id = request.POST.get("titulaire", "")
        classe.titulaire = User.objects.filter(pk=titulaire_id).first() if titulaire_id else None
        classe.effectif = int(request.POST.get("effectif", 0))
        classe.statut = request.POST.get("statut", classe.statut)
        classe.updated_by = request.user
        classe.save()
        messages.success(request, f"Classe '{classe.nom}' modifiée.")
        return redirect("academic:classe_list")


class ClasseDeleteView(RoleRequiredMixin, View):
    """Suppression d'une classe."""
    allowed_roles = [UserRole.ADMIN]

    def post(self, request, pk):
        classe = get_object_or_404(Classe, pk=pk)
        nom = classe.nom
        classe.soft_delete(user=request.user)
        messages.success(request, f"Classe '{nom}' supprimée.")
        return redirect("academic:classe_list")


class CoursEditView(RoleRequiredMixin, View):
    """Édition d'un cours."""
    allowed_roles = [UserRole.ADMIN]
    template_name = "pages/admin/cours/ajouter.html"

    def get(self, request, pk):
        cours = get_object_or_404(Cours, pk=pk)
        from apps.accounts.models import User
        ctx = {
            "page_title": "Modifier le cours",
            "page_subtitle": f"Édition de '{cours.nom}'",
            "cours": cours,
            "classes": Classe.objects.all(),
            "enseignants": User.objects.filter(role=UserRole.ENSEIGNANT, is_active=True),
            "statut_choices": Cours.Statut.choices,
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk):
        cours = get_object_or_404(Cours, pk=pk)
        cours.nom = request.POST.get("nom", cours.nom).strip()
        cours.code = request.POST.get("code", cours.code).strip()
        cours.classe = get_object_or_404(Classe, pk=request.POST.get("classe", cours.classe_id))
        enseignant_id = request.POST.get("enseignant", "")
        cours.enseignant = User.objects.filter(pk=enseignant_id).first() if enseignant_id else None
        cours.coefficient = int(request.POST.get("coefficient", 1))
        cours.description = request.POST.get("description", "").strip()
        cours.statut = request.POST.get("statut", cours.statut)
        cours.updated_by = request.user
        cours.save()
        messages.success(request, f"Cours '{cours.nom}' modifié.")
        return redirect("academic:cours_list")


class CoursDeleteView(RoleRequiredMixin, View):
    """Suppression d'un cours."""
    allowed_roles = [UserRole.ADMIN]

    def post(self, request, pk):
        cours = get_object_or_404(Cours, pk=pk)
        nom = cours.nom
        cours.soft_delete(user=request.user)
        messages.success(request, f"Cours '{nom}' supprimé.")
        return redirect("academic:cours_list")


class EvaluationEditView(RoleRequiredMixin, View):
    """Édition d'une évaluation."""
    allowed_roles = [UserRole.ADMIN, UserRole.ENSEIGNANT]
    template_name = "pages/admin/evaluation/ajouter.html"

    def get(self, request, pk):
        evaluation = get_object_or_404(Evaluation, pk=pk)
        from apps.accounts.models import User
        ctx = {
            "page_title": "Modifier l'évaluation",
            "page_subtitle": f"Édition de '{evaluation.titre}'",
            "evaluation": evaluation,
            "classes": Classe.objects.all(),
            "cours_list": Cours.objects.select_related("classe").all(),
            "enseignants": User.objects.filter(role=UserRole.ENSEIGNANT, is_active=True),
            "type_choices": Evaluation.Type.choices,
            "statut_choices": Evaluation.Statut.choices,
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk):
        evaluation = get_object_or_404(Evaluation, pk=pk)
        evaluation.titre = request.POST.get("titre", evaluation.titre).strip()
        evaluation.type = request.POST.get("type", evaluation.type)
        evaluation.classe = get_object_or_404(Classe, pk=request.POST.get("classe", evaluation.classe_id))
        evaluation.cours = get_object_or_404(Cours, pk=request.POST.get("cours", evaluation.cours_id))
        enseignant_id = request.POST.get("enseignant", "")
        evaluation.enseignant = User.objects.filter(pk=enseignant_id).first() if enseignant_id else evaluation.enseignant
        date_eval = request.POST.get("date_evaluation", "")
        if date_eval:
            from datetime import datetime
            try:
                evaluation.date_evaluation = datetime.strptime(date_eval, "%Y-%m-%d").date()
            except ValueError:
                pass
        evaluation.duree_minutes = int(request.POST.get("duree_minutes", 60))
        evaluation.sur = int(request.POST.get("sur", 20))
        evaluation.description = request.POST.get("description", "").strip()
        evaluation.statut = request.POST.get("statut", evaluation.statut)
        evaluation.updated_by = request.user
        evaluation.save()
        messages.success(request, f"Évaluation '{evaluation.titre}' modifiée.")
        return redirect("academic:evaluation_list")


class EvaluationDeleteView(RoleRequiredMixin, View):
    """Suppression d'une évaluation."""
    allowed_roles = [UserRole.ADMIN, UserRole.ENSEIGNANT]

    def post(self, request, pk):
        evaluation = get_object_or_404(Evaluation, pk=pk)
        titre = evaluation.titre
        evaluation.soft_delete(user=request.user)
        messages.success(request, f"Évaluation '{titre}' supprimée.")
        return redirect("academic:evaluation_list")
