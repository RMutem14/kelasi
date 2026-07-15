"""
Vues de l'application students.

Notes de l'élève et accès aux ressources.
"""
from django.views.generic import ListView

from apps.accounts.enums import UserRole
from apps.core.mixins import RoleRequiredMixin
from apps.students.models import Note, ResourceAccess


class MyNotesView(RoleRequiredMixin, ListView):
    """Notes de l'élève connecté."""
    model = Note
    template_name = "pages/students/notes.html"
    context_object_name = "notes"
    allowed_roles = [UserRole.ELEVE]

    def get_queryset(self):
        return Note.objects.filter(
            eleve=self.request.user
        ).select_related("evaluation", "evaluation__cours", "evaluation__classe").order_by("-date_saisie")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Mes notes"
        ctx["page_subtitle"] = "Suivez vos résultats scolaires."
        notes = self.get_queryset()
        if notes:
            total_points = sum(float(n.valeur) for n in notes)
            total_max = sum(float(n.evaluation.sur) for n in notes)
            ctx["moyenne"] = (total_points / total_max * 20) if total_max > 0 else 0
        else:
            ctx["moyenne"] = 0
        ctx["stats"] = {
            "total": notes.count(),
            "moyenne": ctx["moyenne"],
        }
        return ctx


class MyResourcesView(RoleRequiredMixin, ListView):
    """Ressources accessibles à l'élève (achetées + gratuites)."""
    model = ResourceAccess
    template_name = "pages/students/resources.html"
    context_object_name = "acces"
    allowed_roles = [UserRole.ELEVE]

    def get_queryset(self):
        return ResourceAccess.objects.filter(
            eleve=self.request.user
        ).select_related("ressource", "ressource__auteur").order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Mes ressources"
        ctx["page_subtitle"] = "Toutes les ressources que vous pouvez télécharger."
        return ctx
