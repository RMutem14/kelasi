"""
Vues de l'application students.

Notes de l'élève, accès aux ressources et bulletins de notes.
"""
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.accounts.enums import UserRole
from apps.academic.models import AnneeScolaire, Classe
from apps.core.mixins import HTMXMixin, RoleRequiredMixin
from apps.students.models import Bulletin, Note, Periode, ResourceAccess
from apps.students.services import (
    ClasseBulletinGenerator,
    publish_all_bulletins,
    publish_bulletin,
)


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


# ============================================================
# BULLETINS — Vues élève
# ============================================================


class MyBulletinsView(RoleRequiredMixin, ListView):
    """Bulletins de l'élève connecté (uniquement publiés)."""
    model = Bulletin
    template_name = "pages/students/bulletins.html"
    context_object_name = "bulletins"
    allowed_roles = [UserRole.ELEVE]
    paginate_by = 10

    def get_queryset(self):
        return Bulletin.objects.filter(
            eleve=self.request.user,
            statut=Bulletin.Statut.PUBLIE,
        ).select_related("periode", "classe", "annee_scolaire").order_by("-periode__ordre")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Mes bulletins"
        ctx["page_subtitle"] = "Consultez vos bulletins de notes par période."
        return ctx


class BulletinPDFView(RoleRequiredMixin, View):
    """Téléchargement PDF d'un bulletin."""

    allowed_roles = [UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES, UserRole.ELEVE]

    def get(self, request, pk):
        bulletin = get_object_or_404(
            Bulletin.objects.select_related(
                "eleve", "classe", "periode", "annee_scolaire"
            ),
            pk=pk,
        )

        # Un élève ne peut télécharger que son propre bulletin publié
        if request.user.role == UserRole.ELEVE:
            if bulletin.eleve_id != request.user.id:
                return HttpResponse("Accès refusé.", status=403)
            if not bulletin.est_publie:
                return HttpResponse("Bulletin non publié.", status=403)

        lignes = bulletin.lignes.select_related("cours").all()

        html = render_to_string("pages/students/bulletin_pdf.html", {
            "bulletin": bulletin,
            "lignes": lignes,
            "etablissement": {
                "nom": "Collège Saint Joseph/Elikya",
                "devise": "Discipline — Travail — Réussite",
                "adresse": "Kinshasa, RDC",
            },
        })

        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html).write_pdf()
        except Exception:
            # Fallback : renvoyer le HTML pour impression navigateur
            return HttpResponse(html, content_type="text/html")

        filename = f"bulletin_{bulletin.eleve.last_name}_{bulletin.periode.libelle}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


# ============================================================
# BULLETINS — Vues admin/directeur
# ============================================================


class BulletinListView(HTMXMixin, RoleRequiredMixin, ListView):
    """Liste des bulletins (admin/directeur) avec filtres HTMX."""
    model = Bulletin
    template_name = "pages/admin/bulletins/index.html"
    partial_template_name = "pages/admin/bulletins/_bulletin_list.html"
    context_object_name = "bulletins"
    allowed_roles = [UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]
    paginate_by = 15

    def get_queryset(self):
        qs = Bulletin.objects.select_related(
            "eleve", "classe", "periode", "annee_scolaire"
        ).all().order_by("-created_at")

        search = self.request.GET.get("search", "").strip()
        if search:
            qs = qs.filter(
                eleve__first_name__icontains=search
            ) | qs.filter(
                eleve__last_name__icontains=search
            )

        classe_id = self.request.GET.get("classe", "")
        if classe_id:
            qs = qs.filter(classe_id=classe_id)

        periode_id = self.request.GET.get("periode", "")
        if periode_id:
            qs = qs.filter(periode_id=periode_id)

        statut = self.request.GET.get("statut", "")
        if statut:
            qs = qs.filter(statut=statut)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Bulletins"
        ctx["page_subtitle"] = "Générez et publiez les bulletins de notes."
        ctx["search_query"] = self.request.GET.get("search", "")
        ctx["active_classe"] = self.request.GET.get("classe", "")
        ctx["active_periode"] = self.request.GET.get("periode", "")
        ctx["active_statut"] = self.request.GET.get("statut", "")
        ctx["classes"] = Classe.objects.all().order_by("nom")
        ctx["periodes"] = Periode.objects.select_related("annee_scolaire").all().order_by("-annee_scolaire__date_debut", "ordre")
        ctx["stats_brouillons"] = Bulletin.objects.filter(statut=Bulletin.Statut.BROUILLON).count()
        ctx["stats_publies"] = Bulletin.objects.filter(statut=Bulletin.Statut.PUBLIE).count()

        # Querystring pour pagination
        qs_parts = []
        for key in ["search", "classe", "periode", "statut"]:
            val = self.request.GET.get(key, "")
            if val:
                qs_parts.append(f"{key}={val}")
        ctx["pagination_querystring"] = "&".join(qs_parts)
        return ctx


class BulletinGenerateView(RoleRequiredMixin, View):
    """Génère les bulletins pour une classe et une période."""

    allowed_roles = [UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]

    def post(self, request):
        classe_id = request.POST.get("classe")
        periode_id = request.POST.get("periode")

        if not classe_id or not periode_id:
            messages.error(request, "Veuillez sélectionner une classe et une période.")
            return redirect("students:bulletin_list")

        classe = get_object_or_404(Classe, pk=classe_id)
        periode = get_object_or_404(Periode, pk=periode_id)

        generator = ClasseBulletinGenerator()
        nb_generes, nb_vides = generator.generate_all(
            classe=classe,
            periode=periode,
            publie_par=request.user,
        )

        messages.success(
            request,
            f"{nb_generes} bulletin(s) généré(s) pour {classe.nom} — {periode.libelle}."
        )
        if nb_vides:
            messages.warning(
                request,
                f"{nb_vides} élève(s) sans note pour cette période."
            )

        return redirect(f"{reverse('students:bulletin_list')}?classe={classe_id}&periode={periode_id}")


class BulletinPublishView(RoleRequiredMixin, View):
    """Publie un bulletin individuel."""

    allowed_roles = [UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]

    def post(self, request, pk):
        bulletin = get_object_or_404(Bulletin, pk=pk)
        publish_bulletin(bulletin, request.user)
        messages.success(request, f"Bulletin de {bulletin.eleve.full_name} publié.")
        return redirect("students:bulletin_list")


class BulletinPublishAllView(RoleRequiredMixin, View):
    """Publie tous les bulletins brouillons d'une classe pour une période."""

    allowed_roles = [UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]

    def post(self, request):
        classe_id = request.POST.get("classe")
        periode_id = request.POST.get("periode")

        if not classe_id or not periode_id:
            messages.error(request, "Classe et période requises.")
            return redirect("students:bulletin_list")

        classe = get_object_or_404(Classe, pk=classe_id)
        periode = get_object_or_404(Periode, pk=periode_id)

        count = publish_all_bulletins(classe, periode, request.user)
        messages.success(request, f"{count} bulletin(s) publié(s) pour {classe.nom}.")
        return redirect(f"{reverse('students:bulletin_list')}?classe={classe_id}&periode={periode_id}")


class PeriodeListView(RoleRequiredMixin, ListView):
    """Liste des périodes (admin/directeur)."""
    model = Periode
    template_name = "pages/admin/bulletins/periodes.html"
    context_object_name = "periodes"
    allowed_roles = [UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]

    def get_queryset(self):
        return Periode.objects.select_related("annee_scolaire").all().order_by(
            "-annee_scolaire__date_debut", "ordre"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Périodes"
        ctx["page_subtitle"] = "Gérez les périodes d'évaluation (termes)."
        ctx["annees"] = AnneeScolaire.objects.all().order_by("-date_debut")
        return ctx


class PeriodeCreateView(RoleRequiredMixin, View):
    """Création d'une période."""

    allowed_roles = [UserRole.ADMIN]

    def post(self, request):
        libelle = request.POST.get("libelle", "").strip()
        ordre = request.POST.get("ordre", "")
        annee_id = request.POST.get("annee_scolaire", "")
        date_debut = request.POST.get("date_debut", "")
        date_fin = request.POST.get("date_fin", "")

        if not all([libelle, ordre, annee_id, date_debut, date_fin]):
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect("students:periode_list")

        annee = get_object_or_404(AnneeScolaire, pk=annee_id)

        Periode.objects.create(
            libelle=libelle,
            ordre=int(ordre),
            annee_scolaire=annee,
            date_debut=date_debut,
            date_fin=date_fin,
            created_by=request.user,
        )
        messages.success(request, f"Période '{libelle}' créée avec succès.")
        return redirect("students:periode_list")


class BulletinPDFViewerView(RoleRequiredMixin, TemplateView):
    """Visionneuse PDF intégrée pour un bulletin."""
    template_name = "pages/pdf/viewer.html"
    allowed_roles = [UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES, UserRole.ELEVE]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        bulletin = get_object_or_404(Bulletin, pk=kwargs["pk"])

        if self.request.user.role == UserRole.ELEVE:
            if bulletin.eleve_id != self.request.user.id:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
            if not bulletin.est_publie:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied

        ctx["page_title"] = f"Bulletin — {bulletin.eleve.full_name}"
        ctx["page_subtitle"] = f"{bulletin.periode.libelle} ({bulletin.annee_scolaire.libelle})"
        ctx["pdf_url"] = reverse("students:bulletin_pdf", kwargs={"pk": str(bulletin.pk)})
        ctx["download_url"] = ctx["pdf_url"]
        ctx["back_url"] = reverse("students:bulletin_list")
        return ctx
