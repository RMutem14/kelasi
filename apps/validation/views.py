"""
Vues de validation des documents par le Directeur des études.

- Liste des documents à valider
- Validation / rejet / demande de correction via HTMX
- Consultation des classes et cours (lecture seule)
"""
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

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
    partial_template_name = "pages/directeur/_documents_list.html"
    context_object_name = "documents"
    allowed_roles = [UserRole.DIRECTEUR_ETUDES]
    paginate_by = 10

    def get_template_names(self):
        if self.request.headers.get("HX-Request") == "true":
            return [self.partial_template_name]
        return super().get_template_names()

    def get_queryset(self):
        qs = DocumentPedagogique.objects.select_related(
            "auteur", "classe", "cours"
        ).filter(
            statut__in=[DocumentStatus.SOUMIS, DocumentStatus.CORRECTION, DocumentStatus.VALIDE, DocumentStatus.REJETE]
        ).order_by("-date_soumission")

        statut = self.request.GET.get("statut", "")
        search = self.request.GET.get("search", "").strip()
        if statut:
            qs = qs.filter(statut=statut)
        if search:
            qs = qs.filter(
                Q(titre__icontains=search) | Q(code__icontains=search) |
                Q(auteur__first_name__icontains=search) | Q(auteur__last_name__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Documents à valider"
        ctx["page_subtitle"] = "Validez ou demandez des corrections sur les documents pédagogiques."
        ctx["active_statut"] = self.request.GET.get("statut", "")
        ctx["search_query"] = self.request.GET.get("search", "")
        ctx["stats"] = {
            "en_attente": DocumentPedagogique.objects.filter(statut=DocumentStatus.SOUMIS).count(),
            "a_corriger": DocumentPedagogique.objects.filter(statut=DocumentStatus.CORRECTION).count(),
            "valides": DocumentPedagogique.objects.filter(statut=DocumentStatus.VALIDE).count(),
            "rejetes": DocumentPedagogique.objects.filter(statut=DocumentStatus.REJETE).count(),
        }
        # Querystring pour la pagination HTMX
        qs_params = []
        if ctx["active_statut"]:
            qs_params.append(f"statut={ctx['active_statut']}")
        if ctx["search_query"]:
            qs_params.append(f"search={ctx['search_query']}")
        ctx["pagination_querystring"] = "&".join(qs_params)
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

        # HTMX : retourner le partial de la liste mise à jour
        if request.headers.get("HX-Request") == "true":
            qs = DocumentPedagogique.objects.select_related(
                "auteur", "classe", "cours"
            ).filter(
                statut__in=[DocumentStatus.SOUMIS, DocumentStatus.CORRECTION, DocumentStatus.VALIDE, DocumentStatus.REJETE]
            ).order_by("-date_soumission")
            statut_filter = request.GET.get("statut", "")
            search = request.GET.get("search", "").strip()
            if statut_filter:
                qs = qs.filter(statut=statut_filter)
            if search:
                qs = qs.filter(
                    Q(titre__icontains=search) | Q(code__icontains=search) |
                    Q(auteur__first_name__icontains=search) | Q(auteur__last_name__icontains=search)
                )
            from django.core.paginator import Paginator
            paginator = Paginator(qs, 10)
            page_obj = paginator.get_page(request.GET.get("page", 1))
            return render(request, "pages/directeur/_documents_list.html", {
                "documents": page_obj,
                "page_obj": page_obj,
                "active_statut": statut_filter,
                "search_query": search,
                "pagination_querystring": "&".join(
                    p for p in [f"statut={statut_filter}" if statut_filter else "", f"search={search}" if search else ""] if p
                ),
            })

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
