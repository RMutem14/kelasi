"""
Vues de gestion des documents pédagogiques.

Liste, création, édition, suppression de documents pour les enseignants et admin.
Gestion de l'upload de fichiers (PDF, DOCX).
"""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from apps.accounts.enums import UserRole
from apps.academic.models import Classe, Cours
from apps.core.constants import DocumentStatus
from apps.core.mixins import RoleRequiredMixin
from apps.pedagogy.models import DocumentPedagogique
from apps.validation.models import ValidationHistory


class DocumentListView(RoleRequiredMixin, ListView):
    """Liste des documents pédagogiques."""
    model = DocumentPedagogique
    template_name = "pages/admin/documents/index.html"
    context_object_name = "documents"
    allowed_roles = [UserRole.ADMIN, UserRole.ENSEIGNANT, UserRole.DIRECTEUR_ETUDES]

    def get_queryset(self):
        user = self.request.user
        qs = DocumentPedagogique.objects.select_related(
            "auteur", "classe", "cours"
        ).all().order_by("-created_at")

        if user.role == UserRole.ENSEIGNANT:
            qs = qs.filter(auteur=user)

        statut = self.request.GET.get("statut", "")
        type_doc = self.request.GET.get("type", "")
        if statut:
            qs = qs.filter(statut=statut)
        if type_doc:
            qs = qs.filter(type=type_doc)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Gestion des documents"
        ctx["page_subtitle"] = "Documents pédagogiques liés aux cours, classes et enseignants."
        ctx["active_statut"] = self.request.GET.get("statut", "")
        ctx["active_type"] = self.request.GET.get("type", "")
        ctx["type_choices"] = DocumentPedagogique.Type.choices
        ctx["statut_choices"] = DocumentStatus.choices
        ctx["stats"] = {
            "total": DocumentPedagogique.objects.count(),
            "valides": DocumentPedagogique.objects.filter(statut=DocumentStatus.VALIDE).count(),
            "en_attente": DocumentPedagogique.objects.filter(statut=DocumentStatus.SOUMIS).count(),
            "brouillons": DocumentPedagogique.objects.filter(statut=DocumentStatus.BROUILLON).count(),
        }
        return ctx


class DocumentDetailView(RoleRequiredMixin, View):
    """Détail d'un document via modal HTMX avec historique de validation."""
    allowed_roles = [UserRole.ADMIN, UserRole.ENSEIGNANT, UserRole.DIRECTEUR_ETUDES]

    def get(self, request, pk):
        doc = get_object_or_404(
            DocumentPedagogique.objects.select_related("auteur", "classe", "cours"),
            pk=pk
        )
        historique = ValidationHistory.objects.filter(document=doc).select_related("action_par").order_by("-created_at")
        return render(request, "pages/admin/documents/_detail_modal.html", {
            "doc": doc,
            "historique": historique,
        })


class DocumentCreateView(RoleRequiredMixin, View):
    """Création d'un document pédagogique avec upload de fichier."""
    allowed_roles = [UserRole.ADMIN, UserRole.ENSEIGNANT]
    template_name = "pages/admin/documents/ajouter.html"

    def get(self, request):
        user = self.request.user
        if user.role == UserRole.ENSEIGNANT:
            classes = Classe.objects.filter(titulaire=user)
            cours_list = Cours.objects.filter(enseignant=user)
        else:
            classes = Classe.objects.all()
            cours_list = Cours.objects.select_related("classe").all()

        ctx = {
            "page_title": "Ajouter un document",
            "page_subtitle": "Créez un document pédagogique (fiche, journal, cahier...).",
            "classes": classes,
            "cours_list": cours_list,
            "type_choices": DocumentPedagogique.Type.choices,
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        titre = request.POST.get("titre", "").strip()
        type_doc = request.POST.get("type", DocumentPedagogique.Type.FICHE_PREPARATION)
        classe_id = request.POST.get("classe", "")
        cours_id = request.POST.get("cours", "")
        description = request.POST.get("description", "").strip()
        action = request.POST.get("action", "save_draft")
        fichier = request.FILES.get("fichier")

        if not titre or not classe_id or not cours_id:
            messages.error(request, "Titre, classe et cours sont obligatoires.")
            return redirect("pedagogy:document_add")

        classe = get_object_or_404(Classe, pk=classe_id)
        cours = get_object_or_404(Cours, pk=cours_id)

        statut = DocumentStatus.BROUILLON
        if action == "submit":
            statut = DocumentStatus.SOUMIS

        from django.utils import timezone
        doc = DocumentPedagogique.objects.create(
            titre=titre, type=type_doc, auteur=request.user,
            classe=classe, cours=cours, description=description,
            statut=statut, fichier=fichier, created_by=request.user,
        )

        if statut == DocumentStatus.SOUMIS:
            doc.date_soumission = timezone.now()
            doc.save()
            messages.success(request, f"Document '{titre}' soumis au Directeur des études.")
        else:
            messages.success(request, f"Brouillon '{titre}' enregistré.")
        return redirect("pedagogy:document_list")


class DocumentEditView(RoleRequiredMixin, View):
    """Édition d'un document pédagogique."""
    allowed_roles = [UserRole.ADMIN, UserRole.ENSEIGNANT]
    template_name = "pages/admin/documents/ajouter.html"

    def get(self, request, pk):
        doc = get_object_or_404(DocumentPedagogique, pk=pk)
        user = request.user
        if user.role == UserRole.ENSEIGNANT and doc.auteur != user:
            messages.error(request, "Vous ne pouvez modifier que vos propres documents.")
            return redirect("pedagogy:document_list")
        if doc.statut == DocumentStatus.VALIDE:
            messages.error(request, "Un document validé ne peut plus être modifié.")
            return redirect("pedagogy:document_list")

        if user.role == UserRole.ENSEIGNANT:
            classes = Classe.objects.filter(titulaire=user)
            cours_list = Cours.objects.filter(enseignant=user)
        else:
            classes = Classe.objects.all()
            cours_list = Cours.objects.select_related("classe").all()

        ctx = {
            "page_title": "Modifier le document",
            "page_subtitle": f"Édition de '{doc.titre}'",
            "doc": doc,
            "classes": classes,
            "cours_list": cours_list,
            "type_choices": DocumentPedagogique.Type.choices,
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk):
        doc = get_object_or_404(DocumentPedagogique, pk=pk)
        if request.user.role == UserRole.ENSEIGNANT and doc.auteur != request.user:
            messages.error(request, "Vous ne pouvez modifier que vos propres documents.")
            return redirect("pedagogy:document_list")
        if doc.statut == DocumentStatus.VALIDE:
            messages.error(request, "Un document validé ne peut plus être modifié.")
            return redirect("pedagogy:document_list")

        doc.titre = request.POST.get("titre", doc.titre).strip()
        doc.type = request.POST.get("type", doc.type)
        doc.classe = get_object_or_404(Classe, pk=request.POST.get("classe", doc.classe_id))
        doc.cours = get_object_or_404(Cours, pk=request.POST.get("cours", doc.cours_id))
        doc.description = request.POST.get("description", "").strip()

        nouveau_fichier = request.FILES.get("fichier")
        if nouveau_fichier:
            doc.fichier = nouveau_fichier

        action = request.POST.get("action", "save_draft")
        if action == "submit" and doc.statut == DocumentStatus.BROUILLON:
            doc.statut = DocumentStatus.SOUMIS
            from django.utils import timezone
            doc.date_soumission = timezone.now()

        doc.save()
        messages.success(request, f"Document '{doc.titre}' modifié.")
        return redirect("pedagogy:document_list")


class DocumentDeleteView(RoleRequiredMixin, View):
    """Suppression (soft delete) d'un document."""
    allowed_roles = [UserRole.ADMIN, UserRole.ENSEIGNANT]

    def post(self, request, pk):
        doc = get_object_or_404(DocumentPedagogique, pk=pk)
        if request.user.role == UserRole.ENSEIGNANT and doc.auteur != request.user:
            messages.error(request, "Vous ne pouvez supprimer que vos propres documents.")
            return redirect("pedagogy:document_list")

        titre = doc.titre
        doc.soft_delete(user=request.user)
        messages.success(request, f"Document '{titre}' supprimé.")
        return redirect("pedagogy:document_list")
