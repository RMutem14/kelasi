"""
Vues de l'application attendance.

Saisie des présences/absences par cours avec HTMX, consultation par élève/parent.
"""
from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.accounts.enums import UserRole
from apps.accounts.models import User
from apps.academic.models import Classe, Cours
from apps.core.mixins import RoleRequiredMixin
from apps.attendance.models import Presence


class AttendanceSaisieView(RoleRequiredMixin, TemplateView):
    """Saisie des présences pour une classe et un cours à une date donnée."""
    template_name = "pages/attendance/saisie.html"
    allowed_roles = [UserRole.ENSEIGNANT, UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Saisie des présences"
        ctx["page_subtitle"] = "Marquez les présents, absents et retards."
        ctx["classes"] = Classe.objects.all().order_by("nom")

        classe_id = self.request.GET.get("classe", "")
        cours_id = self.request.GET.get("cours", "")
        date_str = self.request.GET.get("date", "")

        if classe_id:
            ctx["active_classe"] = classe_id
            ctx["cours_list"] = Cours.objects.filter(classe_id=classe_id).order_by("nom")
            ctx["eleves"] = User.objects.filter(
                role=UserRole.ELEVE,
                is_active=True,
            ).order_by("last_name", "first_name")

            if cours_id and date_str:
                ctx["active_cours"] = cours_id
                ctx["active_date"] = date_str
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

                # Récupère les présences existantes
                presences = Presence.objects.filter(
                    cours_id=cours_id,
                    date=date_obj,
                ).select_related("eleve")
                presences_map = {p.eleve_id: p for p in presences}
                ctx["presences_map"] = presences_map
        else:
            ctx["cours_list"] = []
            ctx["eleves"] = []

        return ctx


class AttendanceSaveView(RoleRequiredMixin, View):
    """Enregistre ou met à jour une présence via HTMX."""

    allowed_roles = [UserRole.ENSEIGNANT, UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]

    def post(self, request):
        eleve_id = request.POST.get("eleve")
        cours_id = request.POST.get("cours")
        date_str = request.POST.get("date")
        statut = request.POST.get("statut", Presence.Statut.PRESENT)
        justification = request.POST.get("justification", "").strip()
        minutes_retard = request.POST.get("minutes_retard", "0")

        if not all([eleve_id, cours_id, date_str]):
            return HttpResponse("Paramètres manquants.", status=400)

        eleve = get_object_or_404(User, pk=eleve_id, role=UserRole.ELEVE)
        cours = get_object_or_404(Cours, pk=cours_id)
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        try:
            minutes_retard = int(minutes_retard) if statut == Presence.Statut.RETARD else 0
        except (ValueError, TypeError):
            minutes_retard = 0

        presence, _created = Presence.objects.update_or_create(
            eleve=eleve,
            cours=cours,
            date=date_obj,
            defaults={
                "classe": cours.classe,
                "statut": statut,
                "justification": justification,
                "minutes_retard": minutes_retard,
                "enregistre_par": request.user,
            },
        )

        # Retourne la ligne mise à jour pour HTMX
        html = render_to_string("attendance/_presence_row.html", {
            "eleve": eleve,
            "presence": presence,
        })
        return HttpResponse(html)


class AttendanceHistoryView(RoleRequiredMixin, ListView):
    """Historique des présences avec filtres."""
    model = Presence
    template_name = "pages/attendance/history.html"
    context_object_name = "presences"
    allowed_roles = [UserRole.ENSEIGNANT, UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]
    paginate_by = 20

    def get_queryset(self):
        qs = Presence.objects.select_related(
            "eleve", "cours", "classe", "enregistre_par"
        ).all().order_by("-date", "eleve__last_name")

        search = self.request.GET.get("search", "").strip()
        if search:
            qs = qs.filter(
                eleve__first_name__icontains=search
            ) | qs.filter(
                eleve__last_name__icontains=search
            )

        statut = self.request.GET.get("statut", "")
        if statut:
            qs = qs.filter(statut=statut)

        classe_id = self.request.GET.get("classe", "")
        if classe_id:
            qs = qs.filter(classe_id=classe_id)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Historique des présences"
        ctx["page_subtitle"] = "Consultez toutes les absences et retards."
        ctx["search_query"] = self.request.GET.get("search", "")
        ctx["active_statut"] = self.request.GET.get("statut", "")
        ctx["active_classe"] = self.request.GET.get("classe", "")
        ctx["classes"] = Classe.objects.all().order_by("nom")
        ctx["statut_choices"] = Presence.Statut.choices
        return ctx


class MyAttendanceView(RoleRequiredMixin, ListView):
    """Présences de l'élève connecté."""
    model = Presence
    template_name = "pages/attendance/my_attendance.html"
    context_object_name = "presences"
    allowed_roles = [UserRole.ELEVE]
    paginate_by = 20

    def get_queryset(self):
        return Presence.objects.filter(
            eleve=self.request.user,
        ).select_related("cours", "classe").order_by("-date")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Mes présences"
        ctx["page_subtitle"] = "Suivez vos absences et retards."
        from django.db.models import Count, Q
        presences = self.get_queryset()
        agg = presences.aggregate(
            total=Count("pk"),
            absents=Count("pk", filter=Q(statut=Presence.Statut.ABSENT)),
            absents_justifies=Count("pk", filter=Q(statut=Presence.Statut.ABSENT_JUSTIFIE)),
            retards=Count("pk", filter=Q(statut=Presence.Statut.RETARD)),
        )
        ctx["stats"] = agg
        return ctx


class ChildAttendanceView(RoleRequiredMixin, ListView):
    """Présences d'un enfant (vue parent)."""
    model = Presence
    template_name = "pages/attendance/child_attendance.html"
    context_object_name = "presences"
    allowed_roles = [UserRole.PARENT]
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        from apps.parents.models import ParentEleve
        self.liaison = get_object_or_404(
            ParentEleve,
            parent=request.user,
            eleve__pk=kwargs["eleve_pk"],
            autorise_consultation=True,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Presence.objects.filter(
            eleve=self.liaison.eleve,
        ).select_related("cours", "classe").order_by("-date")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = f"Présences — {self.liaison.eleve.full_name}"
        ctx["page_subtitle"] = f"Relation : {self.liaison.get_relation_display()}"
        ctx["eleve"] = self.liaison.eleve
        from django.db.models import Count, Q
        presences = self.get_queryset()
        agg = presences.aggregate(
            total=Count("pk"),
            absents=Count("pk", filter=Q(statut=Presence.Statut.ABSENT)),
            retards=Count("pk", filter=Q(statut=Presence.Statut.RETARD)),
        )
        ctx["stats"] = agg
        return ctx
