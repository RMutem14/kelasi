"""
Vues de l'application parents.

Dashboard parent, gestion des enfants liés, consultation des notes/bulletins.
"""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.accounts.enums import UserRole
from apps.accounts.models import User
from apps.core.mixins import RoleRequiredMixin
from apps.parents.models import ParentEleve
from apps.students.models import Bulletin, Note


class ParentDashboardView(RoleRequiredMixin, TemplateView):
    """Dashboard du parent : vue d'ensemble de ses enfants."""
    template_name = "pages/parents/dashboard.html"
    allowed_roles = [UserRole.PARENT]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Tableau de bord"
        ctx["page_subtitle"] = "Suivez la scolarité de vos enfants."

        liaisons = ParentEleve.objects.filter(
            parent=self.request.user,
            autorise_consultation=True,
        ).select_related("eleve")

        enfants_data = []
        for liaison in liaisons:
            eleve = liaison.eleve
            dernier_bulletin = Bulletin.objects.filter(
                eleve=eleve,
                statut=Bulletin.Statut.PUBLIE,
            ).order_by("-periode__ordre").first()

            nb_notes = Note.objects.filter(eleve=eleve).count()
            classe = eleve.classes_titulaires.first() if hasattr(eleve, "classes_titulaires") else None

            enfants_data.append({
                "liaison": liaison,
                "eleve": eleve,
                "classe": classe,
                "dernier_bulletin": dernier_bulletin,
                "nb_notes": nb_notes,
            })

        ctx["enfants_data"] = enfants_data
        ctx["stats"] = {
            "total_enfants": len(enfants_data),
            "total_notes": sum(e["nb_notes"] for e in enfants_data),
            "bulletins_disponibles": sum(1 for e in enfants_data if e["dernier_bulletin"]),
        }
        return ctx


class ParentChildrenView(RoleRequiredMixin, ListView):
    """Liste des enfants liés au parent avec gestion."""
    model = ParentEleve
    template_name = "pages/parents/children.html"
    context_object_name = "liaisons"
    allowed_roles = [UserRole.PARENT]

    def get_queryset(self):
        return ParentEleve.objects.filter(
            parent=self.request.user,
        ).select_related("eleve").order_by("eleve__last_name", "eleve__first_name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Mes enfants"
        ctx["page_subtitle"] = "Gérez les liaisons avec vos enfants inscrits."
        # Élèves non encore liés pour le formulaire d'ajout
        linked_ids = self.get_queryset().values_list("eleve_id", flat=True)
        ctx["eleves_disponibles"] = User.objects.filter(
            role=UserRole.ELEVE,
            is_active=True,
        ).exclude(pk__in=linked_ids).order_by("last_name", "first_name")
        ctx["relation_choices"] = ParentEleve.Relation.choices
        return ctx


class LinkChildView(RoleRequiredMixin, View):
    """Lie un enfant au parent connecté."""

    allowed_roles = [UserRole.PARENT]

    def post(self, request):
        eleve_id = request.POST.get("eleve", "")
        relation = request.POST.get("relation", ParentEleve.Relation.TUTEUR)
        est_contact_principal = request.POST.get("est_contact_principal") == "on"

        if not eleve_id:
            messages.error(request, "Veuillez sélectionner un élève.")
            return redirect("parents:children")

        eleve = get_object_or_404(User, pk=eleve_id, role=UserRole.ELEVE, is_active=True)

        # Vérifie qu'un parent n'a pas déjà cet enfant lié
        if ParentEleve.objects.filter(parent=request.user, eleve=eleve).exists():
            messages.error(request, f"{eleve.full_name} est déjà dans votre liste.")
            return redirect("parents:children")

        # Si contact principal, retire le flag des autres liaisons de cet élève
        if est_contact_principal:
            ParentEleve.objects.filter(eleve=eleve, est_contact_principal=True).update(est_contact_principal=False)

        ParentEleve.objects.create(
            parent=request.user,
            eleve=eleve,
            relation=relation,
            est_contact_principal=est_contact_principal,
            created_by=request.user,
        )
        messages.success(request, f"{eleve.full_name} ajouté(e) à vos enfants.")
        return redirect("parents:children")


class UnlinkChildView(RoleRequiredMixin, View):
    """Supprime une liaison parent-enfant."""

    allowed_roles = [UserRole.PARENT]

    def post(self, request, pk):
        liaison = get_object_or_404(ParentEleve, pk=pk, parent=request.user)
        nom = liaison.eleve.full_name
        liaison.delete()
        messages.success(request, f"{nom} retiré(e) de vos enfants.")
        return redirect("parents:children")


class ChildBulletinsView(RoleRequiredMixin, ListView):
    """Bulletins d'un enfant spécifique (consultation parent)."""
    model = Bulletin
    template_name = "pages/parents/child_bulletins.html"
    context_object_name = "bulletins"
    allowed_roles = [UserRole.PARENT]
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        self.liaison = get_object_or_404(
            ParentEleve,
            parent=request.user,
            eleve__pk=kwargs["eleve_pk"],
            autorise_consultation=True,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Bulletin.objects.filter(
            eleve=self.liaison.eleve,
            statut=Bulletin.Statut.PUBLIE,
        ).select_related("periode", "classe", "annee_scolaire").order_by("-periode__ordre")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = f"Bulletins — {self.liaison.eleve.full_name}"
        ctx["page_subtitle"] = f"Relation : {self.liaison.get_relation_display()}"
        ctx["eleve"] = self.liaison.eleve
        ctx["liaison"] = self.liaison
        return ctx


class ChildNotesView(RoleRequiredMixin, ListView):
    """Notes d'un enfant spécifique (consultation parent)."""
    model = Note
    template_name = "pages/parents/child_notes.html"
    context_object_name = "notes"
    allowed_roles = [UserRole.PARENT]
    paginate_by = 15

    def dispatch(self, request, *args, **kwargs):
        self.liaison = get_object_or_404(
            ParentEleve,
            parent=request.user,
            eleve__pk=kwargs["eleve_pk"],
            autorise_consultation=True,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Note.objects.filter(
            eleve=self.liaison.eleve,
        ).select_related("evaluation", "evaluation__cours", "evaluation__classe").order_by("-date_saisie")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = f"Notes — {self.liaison.eleve.full_name}"
        ctx["page_subtitle"] = f"Relation : {self.liaison.get_relation_display()}"
        ctx["eleve"] = self.liaison.eleve
        ctx["liaison"] = self.liaison

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
