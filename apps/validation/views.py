"""
Vues de validation des documents par le Directeur des études.

- Liste des documents à valider
- Validation / rejet / demande de correction via HTMX
- Consultation des classes et cours (lecture seule)
"""
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.accounts.enums import UserRole
from apps.academic.models import Classe, Cours
from apps.core.constants import DocumentStatus
from apps.core.mixins import RoleRequiredMixin
from apps.pedagogy.models import DocumentPedagogique
from apps.validation.models import ValidationHistory


class DocumentValidationListView(RoleRequiredMixin, ListView):
    """Liste des documents à valider par le directeur."""
    model = DocumentPedagogique
    template_name = "pages/directeur/documents.html"
    context_object_name = "documents"
    allowed_roles = [UserRole.DIRECTEUR_ETUDES]

    def get_queryset(self):
        qs = DocumentPedagogique.objects.select_related(
            "auteur", "classe", "cours"
        ).filter(
            statut__in=[DocumentStatus.SOUMIS, DocumentStatus.CORRECTION]
        ).order_by("-date_soumission")

        statut = self.request.GET.get("statut", "")
        if statut:
            qs = qs.filter(statut=statut)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Documents à valider"
        ctx["page_subtitle"] = "Validez ou demandez des corrections sur les documents pédagogiques."
        ctx["active_statut"] = self.request.GET.get("statut", "")
        ctx["stats"] = {
            "en_attente": DocumentPedagogique.objects.filter(statut=DocumentStatus.SOUMIS).count(),
            "a_corriger": DocumentPedagogique.objects.filter(statut=DocumentStatus.CORRECTION).count(),
            "valides": DocumentPedagogique.objects.filter(statut=DocumentStatus.VALIDE).count(),
            "rejetes": DocumentPedagogique.objects.filter(statut=DocumentStatus.REJETE).count(),
        }
        return ctx


class DocumentValidationActionView(RoleRequiredMixin, View):
    """Valide, rejette ou demande une correction sur un document."""
    allowed_roles = [UserRole.DIRECTEUR_ETUDES]

    def post(self, request, pk):
        doc = get_object_or_404(DocumentPedagogique, pk=pk)
        action = request.POST.get("action", "")
        commentaire = request.POST.get("commentaire", "").strip()

        action_map = {
            "validate": DocumentStatus.VALIDE,
            "reject": DocumentStatus.REJETE,
            "correction": DocumentStatus.CORRECTION,
        }

        if action not in action_map:
            messages.error(request, "Action non reconnue.")
            return redirect("validation:document_list")

        new_statut = action_map[action]
        doc.statut = new_statut
        doc.observation_directeur = commentaire

        if new_statut == DocumentStatus.VALIDE:
            doc.date_validation = timezone.now()

        doc.save(update_fields=["statut", "observation_directeur", "date_validation", "updated_at"])

        # Enregistrer dans l'historique
        ValidationHistory.objects.create(
            document=doc,
            action_par=request.user,
            action=new_statut,
            commentaire=commentaire,
        )

        action_labels = {
            "validate": "validé",
            "reject": "rejeté",
            "correction": "renvoyé pour correction",
        }
        messages.success(request, f"Document '{doc.titre}' {action_labels[action]}.")
        return redirect("validation:document_list")


class DirecteurClassesView(RoleRequiredMixin, ListView):
    """Consultation des classes par le directeur (lecture seule)."""
    model = Classe
    template_name = "pages/directeur/classes.html"
    context_object_name = "classes"
    allowed_roles = [UserRole.DIRECTEUR_ETUDES]

    def get_queryset(self):
        return Classe.objects.select_related("titulaire", "annee_scolaire").all().order_by("nom")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Consultation des classes"
        ctx["page_subtitle"] = "Lecture uniquement — vous ne pouvez pas modifier les classes."
        return ctx


class DirecteurCoursView(RoleRequiredMixin, ListView):
    """Consultation des cours par le directeur (lecture seule)."""
    model = Cours
    template_name = "pages/directeur/cours.html"
    context_object_name = "cours_list"
    allowed_roles = [UserRole.DIRECTEUR_ETUDES]

    def get_queryset(self):
        return Cours.objects.select_related("classe", "enseignant").all().order_by("classe__nom", "nom")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Consultation des cours"
        ctx["page_subtitle"] = "Lecture uniquement — vous ne pouvez pas modifier les cours."
        return ctx
