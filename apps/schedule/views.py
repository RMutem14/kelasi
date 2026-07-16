"""
Vues de l'application schedule.

Vue calendrier de l'emploi du temps, création de créneaux avec détection de conflits.
"""
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.enums import UserRole
from apps.accounts.models import User
from apps.academic.models import AnneeScolaire, Classe, Cours
from apps.core.mixins import RoleRequiredMixin
from apps.schedule.models import Creneau


class ScheduleView(RoleRequiredMixin, TemplateView):
    """Vue calendrier de l'emploi du temps par classe."""
    template_name = "pages/schedule/timetable.html"
    allowed_roles = [UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES, UserRole.ENSEIGNANT, UserRole.ELEVE]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Emploi du temps"
        ctx["page_subtitle"] = "Planning hebdomadaire des cours."
        ctx["classes"] = Classe.objects.all().order_by("nom")
        ctx["jours"] = Creneau.Jour.choices

        # Heures de 7h à 18h par tranches d'1h
        heures = [f"{h:02d}:00" for h in range(7, 19)]
        ctx["heures"] = heures

        classe_id = self.request.GET.get("classe", "")
        annee_active = AnneeScolaire.objects.filter(est_active=True).first()
        if not annee_active:
            annee_active = AnneeScolaire.objects.order_by("-date_debut").first()

        if classe_id:
            ctx["active_classe"] = classe_id
            creneaux = Creneau.objects.filter(
                classe_id=classe_id,
                annee_scolaire=annee_active,
            ).select_related("cours", "enseignant", "classe")
        elif self.request.user.role == UserRole.ENSEIGNANT:
            creneaux = Creneau.objects.filter(
                enseignant=self.request.user,
                annee_scolaire=annee_active,
            ).select_related("cours", "enseignant", "classe")
        elif self.request.user.role == UserRole.ELEVE:
            # Pour l'élève, on affiche sa classe
            classe = self.request.user.classes_titulaires.first() if hasattr(self.request.user, "classes_titulaires") else None
            if classe:
                creneaux = Creneau.objects.filter(
                    classe=classe,
                    annee_scolaire=annee_active,
                ).select_related("cours", "enseignant", "classe")
            else:
                creneaux = Creneau.objects.none()
        else:
            creneaux = Creneau.objects.none()

        # Organise par jour et heure
        grille = {}
        for creneau in creneaux:
            jour = creneau.jour
            heure_key = creneau.heure_debut.strftime("%H:%M")
            if jour not in grille:
                grille[jour] = {}
            grille[jour][heure_key] = creneau

        ctx["grille"] = grille
        ctx["annee_active"] = annee_active

        # Pour le formulaire de création (admin/directeur)
        if self.request.user.role in [UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]:
            ctx["cours_list"] = Cours.objects.all().order_by("nom")
            ctx["enseignants"] = User.objects.filter(
                role=UserRole.ENSEIGNANT, is_active=True
            ).order_by("last_name", "first_name")
            ctx["annees"] = AnneeScolaire.objects.all().order_by("-date_debut")

        return ctx


class CreneauCreateView(RoleRequiredMixin, View):
    """Création d'un créneau avec détection de conflits."""

    allowed_roles = [UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]

    def post(self, request):
        classe_id = request.POST.get("classe", "")
        cours_id = request.POST.get("cours", "")
        enseignant_id = request.POST.get("enseignant", "")
        jour = request.POST.get("jour", "")
        heure_debut = request.POST.get("heure_debut", "")
        heure_fin = request.POST.get("heure_fin", "")
        salle = request.POST.get("salle", "").strip()
        annee_id = request.POST.get("annee_scolaire", "")

        if not all([classe_id, cours_id, enseignant_id, jour, heure_debut, heure_fin, annee_id]):
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect("schedule:timetable")

        classe = get_object_or_404(Classe, pk=classe_id)
        cours = get_object_or_404(Cours, pk=cours_id)
        enseignant = get_object_or_404(User, pk=enseignant_id, role=UserRole.ENSEIGNANT)
        annee = get_object_or_404(AnneeScolaire, pk=annee_id)

        from datetime import datetime
        try:
            hd = datetime.strptime(heure_debut, "%H:%M").time()
            hf = datetime.strptime(heure_fin, "%H:%M").time()
        except ValueError:
            messages.error(request, "Format d'heure invalide.")
            return redirect("schedule:timetable")

        if hd >= hf:
            messages.error(request, "L'heure de début doit être antérieure à l'heure de fin.")
            return redirect("schedule:timetable")

        creneau = Creneau(
            classe=classe,
            cours=cours,
            enseignant=enseignant,
            jour=jour,
            heure_debut=hd,
            heure_fin=hf,
            salle=salle,
            annee_scolaire=annee,
            created_by=request.user,
        )

        conflits = creneau.detecter_conflits()
        if conflits:
            messages.error(
                request,
                "Conflit détecté : " + " | ".join(c["message"] for c in conflits)
            )
            return redirect(f"{reverse('schedule:timetable')}?classe={classe_id}")

        creneau.save()
        messages.success(request, f"Créneau ajouté : {cours.nom} — {jour} {heure_debut}-{heure_fin}")
        return redirect(f"{reverse('schedule:timetable')}?classe={classe_id}")


class CreneauDeleteView(RoleRequiredMixin, View):
    """Suppression d'un créneau."""

    allowed_roles = [UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]

    def post(self, request, pk):
        creneau = get_object_or_404(Creneau, pk=pk)
        creneau.delete()
        messages.success(request, "Créneau supprimé.")
        return redirect("schedule:timetable")


class CreneauConflitCheckView(RoleRequiredMixin, View):
    """Vérification de conflits en AJAX/HTMX."""

    allowed_roles = [UserRole.ADMIN, UserRole.DIRECTEUR_ETUDES]

    def get(self, request):
        classe_id = request.GET.get("classe", "")
        enseignant_id = request.GET.get("enseignant", "")
        jour = request.GET.get("jour", "")
        heure_debut = request.GET.get("heure_debut", "")
        heure_fin = request.GET.get("heure_fin", "")
        salle = request.GET.get("salle", "")
        annee_id = request.GET.get("annee_scolaire", "")

        if not all([jour, heure_debut, heure_fin, annee_id]):
            return JsonResponse({"conflits": []})

        from datetime import datetime
        try:
            hd = datetime.strptime(heure_debut, "%H:%M").time()
            hf = datetime.strptime(heure_fin, "%H:%M").time()
        except ValueError:
            return JsonResponse({"conflits": [], "error": "Format invalide"})

        temp = Creneau(
            jour=jour,
            heure_debut=hd,
            heure_fin=hf,
            salle=salle,
            annee_scolaire_id=annee_id,
            classe_id=classe_id or None,
            enseignant_id=enseignant_id or None,
        )

        conflits = temp.detecter_conflits()
        return JsonResponse({
            "conflits": [
                {"type": c["type"], "message": c["message"]}
                for c in conflits
            ]
        })
