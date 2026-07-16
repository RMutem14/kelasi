"""
Vues de l'application finance.

Gestion des frais de scolarité, paiements et tableau de bord financier.
"""
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.accounts.enums import UserRole
from apps.accounts.models import User
from apps.academic.models import AnneeScolaire
from apps.core.mixins import HTMXMixin, RoleRequiredMixin
from apps.finance.models import FraisEleve, FraisType, Paiement


class FinanceDashboardView(RoleRequiredMixin, TemplateView):
    """Tableau de bord financier (admin)."""
    template_name = "pages/admin/finance/dashboard.html"
    allowed_roles = [UserRole.ADMIN]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Frais de scolarité"
        ctx["page_subtitle"] = "Suivi financier de l'établissement."

        annee_active = AnneeScolaire.objects.filter(est_active=True).first()
        if not annee_active:
            annee_active = AnneeScolaire.objects.order_by("-date_debut").first()

        frais_qs = FraisEleve.objects.filter(annee_scolaire=annee_active) if annee_active else FraisEleve.objects.none()

        total_attendu = frais_qs.aggregate(total=Sum("montant_total"))["total"] or Decimal("0")
        total_paye = frais_qs.aggregate(total=Sum("montant_paye"))["total"] or Decimal("0")
        total_restant = total_attendu - total_paye

        ctx["annee_active"] = annee_active
        ctx["stats"] = {
            "total_attendu": total_attendu,
            "total_paye": total_paye,
            "total_restant": total_restant,
            "taux_recouvrement": (float(total_paye) / float(total_attendu) * 100) if total_attendu > 0 else 0,
            "nb_en_attente": frais_qs.filter(statut=FraisEleve.Statut.EN_ATTENTE).count(),
            "nb_partiellement": frais_qs.filter(statut=FraisEleve.Statut.PARTIELLEMENT_PAYE).count(),
            "nb_paye": frais_qs.filter(statut=FraisEleve.Statut.PAYE).count(),
            "nb_en_retard": frais_qs.filter(statut=FraisEleve.Statut.EN_RETARD).count(),
        }

        # Paiements récents
        ctx["paiements_recents"] = Paiement.objects.select_related(
            "frais_eleve__eleve", "enregistre_par"
        ).all().order_by("-date_paiement")[:10]

        # Répartition par catégorie
        ctx["par_categorie"] = []
        for cat_val, cat_label in FraisType.Categorie.choices:
            frais_cat = frais_qs.filter(frais_type__categorie=cat_val)
            attendu = frais_cat.aggregate(t=Sum("montant_total"))["t"] or Decimal("0")
            paye = frais_cat.aggregate(t=Sum("montant_paye"))["t"] or Decimal("0")
            if attendu > 0:
                ctx["par_categorie"].append({
                    "label": cat_label,
                    "attendu": attendu,
                    "paye": paye,
                    "taux": (float(paye) / float(attendu) * 100) if attendu > 0 else 0,
                })

        return ctx


class FraisTypeListView(RoleRequiredMixin, ListView):
    """Liste des types de frais."""
    model = FraisType
    template_name = "pages/admin/finance/frais_types.html"
    context_object_name = "frais_types"
    allowed_roles = [UserRole.ADMIN]

    def get_queryset(self):
        return FraisType.objects.select_related("annee_scolaire").all().order_by(
            "-annee_scolaire__date_debut", "categorie", "libelle"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Types de frais"
        ctx["page_subtitle"] = "Configurez les frais applicables aux élèves."
        ctx["annees"] = AnneeScolaire.objects.all().order_by("-date_debut")
        ctx["categorie_choices"] = FraisType.Categorie.choices
        return ctx


class FraisTypeCreateView(RoleRequiredMixin, View):
    """Création d'un type de frais."""

    allowed_roles = [UserRole.ADMIN]

    def post(self, request):
        libelle = request.POST.get("libelle", "").strip()
        categorie = request.POST.get("categorie", FraisType.Categorie.SCOLARITE)
        montant = request.POST.get("montant", "")
        annee_id = request.POST.get("annee_scolaire", "")
        est_obligatoire = request.POST.get("est_obligatoire") == "on"
        est_recurrent = request.POST.get("est_recurrent") == "on"
        description = request.POST.get("description", "").strip()

        if not all([libelle, montant, annee_id]):
            messages.error(request, "Libellé, montant et année scolaire sont obligatoires.")
            return redirect("finance:frais_type_list")

        annee = get_object_or_404(AnneeScolaire, pk=annee_id)

        FraisType.objects.create(
            libelle=libelle,
            categorie=categorie,
            montant=Decimal(montant),
            annee_scolaire=annee,
            est_obligatoire=est_obligatoire,
            est_recurrent=est_recurrent,
            description=description,
            created_by=request.user,
        )
        messages.success(request, f"Type de frais '{libelle}' créé avec succès.")
        return redirect("finance:frais_type_list")


class FraisEleveListView(HTMXMixin, RoleRequiredMixin, ListView):
    """Liste des frais par élève avec filtres HTMX."""
    model = FraisEleve
    template_name = "pages/admin/finance/frais_eleves.html"
    partial_template_name = "pages/admin/finance/_frais_eleve_list.html"
    context_object_name = "frais_list"
    allowed_roles = [UserRole.ADMIN]
    paginate_by = 15

    def get_queryset(self):
        qs = FraisEleve.objects.select_related(
            "eleve", "frais_type", "annee_scolaire"
        ).all().order_by("-created_at")

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

        annee_id = self.request.GET.get("annee", "")
        if annee_id:
            qs = qs.filter(annee_scolaire_id=annee_id)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Frais par élève"
        ctx["page_subtitle"] = "Suivez les paiements de chaque élève."
        ctx["search_query"] = self.request.GET.get("search", "")
        ctx["active_statut"] = self.request.GET.get("statut", "")
        ctx["active_annee"] = self.request.GET.get("annee", "")
        ctx["annees"] = AnneeScolaire.objects.all().order_by("-date_debut")
        ctx["statut_choices"] = FraisEleve.Statut.choices
        ctx["frais_types_available"] = FraisType.objects.select_related("annee_scolaire").all().order_by("libelle")

        qs_parts = []
        for key in ["search", "statut", "annee"]:
            val = self.request.GET.get(key, "")
            if val:
                qs_parts.append(f"{key}={val}")
        ctx["pagination_querystring"] = "&".join(qs_parts)
        return ctx


class FraisElevePaymentView(RoleRequiredMixin, View):
    """Enregistre un paiement pour un frais élève."""

    allowed_roles = [UserRole.ADMIN]

    def post(self, request, pk):
        frais = get_object_or_404(FraisEleve, pk=pk)

        montant = request.POST.get("montant", "")
        methode = request.POST.get("methode", Paiement.Methode.ESPECES)
        reference = request.POST.get("reference", "").strip()

        if not montant:
            messages.error(request, "Le montant est obligatoire.")
            return redirect("finance:frais_eleve_list")

        try:
            montant = Decimal(montant)
        except (ValueError, TypeError):
            messages.error(request, "Montant invalide.")
            return redirect("finance:frais_eleve_list")

        if montant <= 0:
            messages.error(request, "Le montant doit être positif.")
            return redirect("finance:frais_eleve_list")

        if montant > frais.montant_restant:
            messages.warning(
                request,
                f"Le montant dépasse le restant dû ({frais.montant_restant} $). Paiement ajusté."
            )
            montant = frais.montant_restant

        with transaction.atomic():
            frais.enregistrer_paiement(
                montant=montant,
                methode=methode,
                reference=reference,
                enregistre_par=request.user,
            )

        messages.success(
            request,
            f"Paiement de {montant} $ enregistré pour {frais.eleve.full_name}."
        )
        return redirect("finance:frais_eleve_list")


class FraisAssignView(RoleRequiredMixin, View):
    """Assigne un type de frais à tous les élèves actifs."""

    allowed_roles = [UserRole.ADMIN]

    def post(self, request):
        frais_type_id = request.POST.get("frais_type", "")
        date_echeance = request.POST.get("date_echeance", "")

        if not frais_type_id:
            messages.error(request, "Veuillez sélectionner un type de frais.")
            return redirect("finance:frais_eleve_list")

        frais_type = get_object_or_404(FraisType, pk=frais_type_id)

        eleves = User.objects.filter(role=UserRole.ELEVE, is_active=True)
        nb_crees = 0
        nb_existants = 0

        for eleve in eleves:
            _, created = FraisEleve.objects.get_or_create(
                eleve=eleve,
                frais_type=frais_type,
                annee_scolaire=frais_type.annee_scolaire,
                defaults={
                    "montant_total": frais_type.montant,
                    "date_echeance": date_echeance or None,
                    "created_by": request.user,
                },
            )
            if created:
                nb_crees += 1
            else:
                nb_existants += 1

        messages.success(
            request,
            f"{nb_crees} frais assigné(s). {nb_existants} déjà existant(s)."
        )
        return redirect("finance:frais_eleve_list")


class PaiementListView(HTMXMixin, RoleRequiredMixin, ListView):
    """Liste des paiements avec filtres HTMX."""
    model = Paiement
    template_name = "pages/admin/finance/paiements.html"
    partial_template_name = "pages/admin/finance/_paiement_list.html"
    context_object_name = "paiements"
    allowed_roles = [UserRole.ADMIN]
    paginate_by = 20

    def get_queryset(self):
        qs = Paiement.objects.select_related(
            "frais_eleve__eleve", "frais_eleve__frais_type", "enregistre_par"
        ).all().order_by("-date_paiement")

        search = self.request.GET.get("search", "").strip()
        if search:
            qs = qs.filter(
                frais_eleve__eleve__first_name__icontains=search
            ) | qs.filter(
                frais_eleve__eleve__last_name__icontains=search
            ) | qs.filter(
                reference__icontains=search
            )

        methode = self.request.GET.get("methode", "")
        if methode:
            qs = qs.filter(methode=methode)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Paiements"
        ctx["page_subtitle"] = "Historique des paiements enregistrés."
        ctx["search_query"] = self.request.GET.get("search", "")
        ctx["active_methode"] = self.request.GET.get("methode", "")
        ctx["methode_choices"] = Paiement.Methode.choices

        qs_parts = []
        for key in ["search", "methode"]:
            val = self.request.GET.get(key, "")
            if val:
                qs_parts.append(f"{key}={val}")
        ctx["pagination_querystring"] = "&".join(qs_parts)

        # Stats globales — reuse queryset to avoid double query
        qs = self.get_queryset()
        ctx["total_paiements"] = qs.aggregate(t=Sum("montant"))["t"] or Decimal("0")
        return ctx
