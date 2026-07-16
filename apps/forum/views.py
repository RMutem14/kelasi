"""
Vues de l'application forum.

Questions/Réponses entre élèves et enseignants avec HTMX.
"""
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import DetailView, ListView

from apps.accounts.enums import UserRole
from apps.academic.models import Cours
from apps.core.mixins import HTMXMixin, RoleRequiredMixin
from apps.forum.models import Question, Reponse


class QuestionListView(HTMXMixin, RoleRequiredMixin, ListView):
    """Liste des questions avec filtres HTMX."""
    model = Question
    template_name = "pages/forum/question_list.html"
    partial_template_name = "pages/forum/_question_list.html"
    context_object_name = "questions"
    allowed_roles = [UserRole.ELEVE, UserRole.ENSEIGNANT, UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]
    paginate_by = 15

    def get_queryset(self):
        qs = Question.objects.select_related("auteur", "cours", "cours__classe").all().order_by("-created_at")

        search = self.request.GET.get("search", "").strip()
        if search:
            qs = qs.filter(titre__icontains=search) | qs.filter(contenu__icontains=search)

        statut = self.request.GET.get("statut", "")
        if statut:
            qs = qs.filter(statut=statut)

        cours_id = self.request.GET.get("cours", "")
        if cours_id:
            qs = qs.filter(cours_id=cours_id)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Forum Q/R"
        ctx["page_subtitle"] = "Posez vos questions et aidez vos camarades."
        ctx["search_query"] = self.request.GET.get("search", "")
        ctx["active_statut"] = self.request.GET.get("statut", "")
        ctx["active_cours"] = self.request.GET.get("cours", "")
        ctx["cours_list"] = Cours.objects.all().order_by("nom")[:20]
        ctx["statut_choices"] = Question.Statut.choices

        qs_parts = []
        for key in ["search", "statut", "cours"]:
            val = self.request.GET.get(key, "")
            if val:
                qs_parts.append(f"{key}={val}")
        ctx["pagination_querystring"] = "&".join(qs_parts)
        return ctx


class QuestionDetailView(RoleRequiredMixin, DetailView):
    """Détail d'une question avec ses réponses."""
    model = Question
    template_name = "pages/forum/question_detail.html"
    context_object_name = "question"
    allowed_roles = [UserRole.ELEVE, UserRole.ENSEIGNANT, UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Incrémenter le compteur de vues (sans trigger updated_at)
        Question.objects.filter(pk=obj.pk).update(vue_count=obj.vue_count + 1)
        obj.vue_count += 1
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = self.object.titre
        ctx["reponses"] = self.object.reponses.select_related("auteur").all().order_by(
            "-est_validee", "created_at"
        )
        return ctx


class QuestionCreateView(RoleRequiredMixin, View):
    """Création d'une question (élève)."""

    allowed_roles = [UserRole.ELEVE]

    def post(self, request):
        titre = request.POST.get("titre", "").strip()
        contenu = request.POST.get("contenu", "").strip()
        cours_id = request.POST.get("cours", "")

        if not titre or not contenu:
            messages.error(request, "Le titre et le contenu sont obligatoires.")
            return redirect("forum:question_list")

        cours = None
        if cours_id:
            cours = get_object_or_404(Cours, pk=cours_id)

        Question.objects.create(
            titre=titre,
            contenu=contenu,
            auteur=request.user,
            cours=cours,
            created_by=request.user,
        )
        messages.success(request, "Votre question a été publiée.")
        return redirect("forum:question_list")


class ReponseCreateView(RoleRequiredMixin, View):
    """Ajout d'une réponse via HTMX."""

    allowed_roles = [UserRole.ELEVE, UserRole.ENSEIGNANT, UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]

    def post(self, request, pk):
        question = get_object_or_404(Question, pk=pk)
        contenu = request.POST.get("contenu", "").strip()

        if not contenu:
            messages.error(request, "La réponse ne peut pas être vide.")
            return redirect("forum:question_detail", pk=pk)

        reponse = Reponse.objects.create(
            question=question,
            auteur=request.user,
            contenu=contenu,
            created_by=request.user,
        )

        # Si HTMX, retourner la réponse partielle
        if request.headers.get("HX-Request") == "true":
            reponses = question.reponses.select_related("auteur").all().order_by(
                "-est_validee", "created_at"
            )
            html = render_to_string("pages/forum/_reponse_list.html", {
                "reponses": reponses,
                "current_user": request.user,
            })
            return HttpResponse(html)

        messages.success(request, "Réponse publiée.")
        return redirect("forum:question_detail", pk=pk)


class ReponseValidateView(RoleRequiredMixin, View):
    """Marque une réponse comme validée (par l'auteur de la question)."""

    allowed_roles = [UserRole.ELEVE, UserRole.ENSEIGNANT, UserRole.ADMIN]

    def post(self, request, pk):
        reponse = get_object_or_404(Reponse, pk=pk)

        # Seul l'auteur de la question ou un admin peut valider
        if reponse.question.auteur_id != request.user.id and not request.user.is_admin:
            messages.error(request, "Vous ne pouvez pas valider cette réponse.")
            return redirect("forum:question_detail", pk=reponse.question_id)

        # Désélectionner l'ancienne réponse validée
        Reponse.objects.filter(question=reponse.question, est_validee=True).update(est_validee=False)
        reponse.est_validee = True
        reponse.save(update_fields=["est_validee"])

        messages.success(request, "Réponse marquée comme correcte.")
        return redirect("forum:question_detail", pk=reponse.question_id)


class QuestionCloseView(RoleRequiredMixin, View):
    """Ferme une question (par l'auteur ou un admin)."""

    allowed_roles = [UserRole.ELEVE, UserRole.ENSEIGNANT, UserRole.ADMIN]

    def post(self, request, pk):
        question = get_object_or_404(Question, pk=pk)

        if question.auteur_id != request.user.id and not request.user.is_admin:
            messages.error(request, "Vous ne pouvez pas fermer cette question.")
            return redirect("forum:question_detail", pk=pk)

        question.statut = Question.Statut.FERMEE
        question.save(update_fields=["statut"])
        messages.success(request, "Question fermée.")
        return redirect("forum:question_detail", pk=pk)
