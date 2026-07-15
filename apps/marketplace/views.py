"""
Vues de l'application marketplace.

Catalogue, publication de ressources, achat simulé, téléchargement.
"""
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from apps.accounts.enums import UserRole
from apps.academic.models import Classe, Cours
from apps.core.constants import PublicationStatus, OrderStatus, ResourceType, ResourceCategory
from apps.core.mixins import RoleRequiredMixin
from apps.marketplace.models import Resource, Order, Download
from apps.students.models import ResourceAccess


class CatalogView(ListView):
    """Catalogue public des ressources publiées (tous les rôles connectés)."""
    model = Resource
    template_name = "pages/marketplace/catalog.html"
    context_object_name = "ressources"
    paginate_by = 12

    def get_queryset(self):
        qs = Resource.objects.select_related("auteur", "classe", "cours").filter(
            statut=PublicationStatus.PUBLIE
        ).order_by("-created_at")
        type_filter = self.request.GET.get("type", "")
        search = self.request.GET.get("search", "").strip()
        if type_filter:
            qs = qs.filter(type=type_filter)
        if search:
            qs = qs.filter(titre__icontains=search)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Catalogue"
        ctx["page_subtitle"] = "Découvrez les ressources pédagogiques disponibles."
        ctx["type_choices"] = ResourceType.choices
        ctx["active_type"] = self.request.GET.get("type", "")
        ctx["search_query"] = self.request.GET.get("search", "")
        return ctx


class ResourceDetailView(View):
    """Détail d'une ressource (fiche complète)."""
    def get(self, request, pk):
        ressource = get_object_or_404(
            Resource.objects.select_related("auteur", "classe", "cours"),
            pk=pk, statut=PublicationStatus.PUBLIE
        )
        ressource.nombre_vues += 1
        ressource.save(update_fields=["nombre_vues"])

        has_access = False
        has_purchased = False
        if request.user.is_authenticated:
            has_access = ResourceAccess.objects.filter(eleve=request.user, ressource=ressource).exists()
            has_purchased = Order.objects.filter(eleve=request.user, ressource=ressource, statut=OrderStatus.PAYE).exists()

        ctx = {
            "ressource": ressource,
            "page_title": ressource.titre,
            "page_subtitle": f"Par {ressource.auteur.full_name}",
            "has_access": has_access,
            "has_purchased": has_purchased,
        }
        return render(request, "pages/marketplace/detail.html", ctx)


class ResourceCreateView(RoleRequiredMixin, View):
    """Publication d'une nouvelle ressource (enseignant)."""
    allowed_roles = [UserRole.ENSEIGNANT, UserRole.ADMIN]
    template_name = "pages/marketplace/publier.html"

    def get(self, request):
        ctx = {
            "page_title": "Publier une ressource",
            "page_subtitle": "Mettez en vente un syllabus, support de cours, exercice...",
            "classes": Classe.objects.all(),
            "cours_list": Cours.objects.select_related("classe").all(),
            "type_choices": ResourceType.choices,
            "category_choices": ResourceCategory.choices,
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        titre = request.POST.get("titre", "").strip()
        description = request.POST.get("description", "").strip()
        type_r = request.POST.get("type", ResourceType.SYLLABUS)
        categorie = request.POST.get("categorie", ResourceCategory.COURS)
        prix = request.POST.get("prix", 0)
        classe_id = request.POST.get("classe", "")
        cours_id = request.POST.get("cours", "")
        fichier = request.FILES.get("fichier")
        action = request.POST.get("action", "save_draft")

        if not titre or not fichier:
            messages.error(request, "Titre et fichier sont obligatoires.")
            return redirect("marketplace:publish")

        classe = Classe.objects.filter(pk=classe_id).first() if classe_id else None
        cours = Cours.objects.filter(pk=cours_id).first() if cours_id else None

        statut = PublicationStatus.BROUILLON
        if action == "publish":
            statut = PublicationStatus.PUBLIE

        ressource = Resource.objects.create(
            titre=titre, description=description, auteur=request.user,
            type=type_r, categorie=categorie, prix=prix,
            classe=classe, cours=cours, fichier=fichier,
            statut=statut, created_by=request.user,
        )

        if statut == PublicationStatus.PUBLIE:
            messages.success(request, f"Ressource '{titre}' publiée dans le catalogue.")
        else:
            messages.success(request, f"Brouillon '{titre}' enregistré.")
        return redirect("marketplace:my_resources")


class MyResourcesView(RoleRequiredMixin, ListView):
    """Ressources publiées par l'enseignant connecté."""
    model = Resource
    template_name = "pages/marketplace/my_resources.html"
    context_object_name = "ressources"
    allowed_roles = [UserRole.ENSEIGNANT, UserRole.ADMIN]

    def get_queryset(self):
        return Resource.objects.filter(auteur=self.request.user).order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Mes ressources"
        ctx["page_subtitle"] = "Gérez vos ressources publiées."
        ctx["stats"] = {
            "total": Resource.objects.filter(auteur=self.request.user).count(),
            "publiees": Resource.objects.filter(auteur=self.request.user, statut=PublicationStatus.PUBLIE).count(),
            "brouillons": Resource.objects.filter(auteur=self.request.user, statut=PublicationStatus.BROUILLON).count(),
            "ventes": Order.objects.filter(ressource__auteur=self.request.user, statut=OrderStatus.PAYE).count(),
        }
        return ctx


class MySalesView(RoleRequiredMixin, ListView):
    """Ventes de l'enseignant connecté."""
    model = Order
    template_name = "pages/marketplace/my_sales.html"
    context_object_name = "commandes"
    allowed_roles = [UserRole.ENSEIGNANT, UserRole.ADMIN]

    def get_queryset(self):
        return Order.objects.filter(
            ressource__auteur=self.request.user, statut=OrderStatus.PAYE
        ).select_related("eleve", "ressource").order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Mes ventes"
        ctx["page_subtitle"] = "Suivez les ventes de vos ressources."
        from django.db.models import Sum
        ventes = Order.objects.filter(ressource__auteur=self.request.user, statut=OrderStatus.PAYE)
        ctx["stats"] = {
            "total_ventes": ventes.count(),
            "revenu_total": ventes.aggregate(total=Sum("montant"))["total"] or 0,
        }
        return ctx


class MyPurchasesView(RoleRequiredMixin, ListView):
    """Achats de l'utilisateur connecté."""
    model = Order
    template_name = "pages/marketplace/my_purchases.html"
    context_object_name = "commandes"
    allowed_roles = [UserRole.ELEVE, UserRole.ENSEIGNANT, UserRole.ADMIN]

    def get_queryset(self):
        return Order.objects.filter(
            eleve=self.request.user
        ).select_related("ressource").order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Mes achats"
        ctx["page_subtitle"] = "Vos commandes et ressources achetées."
        return ctx


class BuyView(RoleRequiredMixin, View):
    """Achat d'une ressource via le PaymentService (scalable)."""
    allowed_roles = [UserRole.ELEVE, UserRole.ENSEIGNANT, UserRole.ADMIN]

    def post(self, request, pk):
        ressource = get_object_or_404(Resource, pk=pk, statut=PublicationStatus.PUBLIE)

        # Vérifier si déjà achetée
        existing_order = Order.objects.filter(
            eleve=request.user, ressource=ressource, statut=OrderStatus.PAYE
        ).first()
        if existing_order:
            messages.info(request, "Vous avez déjà accès à cette ressource.")
            return redirect("marketplace:detail", pk=ressource.pk)

        # Créer la commande (en attente de paiement)
        order = Order.objects.create(
            eleve=request.user,
            ressource=ressource,
            montant=ressource.prix,
            statut=OrderStatus.EN_ATTENTE,
            created_by=request.user,
        )

        # Traiter le paiement via le service (passerelle configurable)
        from apps.marketplace.payments import PaymentService
        service = PaymentService()
        result = service.process_payment(order=order, user=request.user)

        if result.success:
            if result.redirect_url:
                # Passerelle réelle : rediriger vers la page de paiement
                return redirect(result.redirect_url)
            else:
                # Paiement simulé : déjà confirmé
                messages.success(request, f"Paiement validé ! Vous pouvez maintenant télécharger '{ressource.titre}'.")
                return redirect("marketplace:download", pk=ressource.pk)
        else:
            messages.error(request, f"Le paiement a échoué : {result.message}")
            return redirect("marketplace:detail", pk=ressource.pk)


class DownloadView(RoleRequiredMixin, View):
    """Téléchargement d'une ressource achetée ou gratuite."""
    allowed_roles = [UserRole.ELEVE, UserRole.ENSEIGNANT, UserRole.ADMIN]

    def get(self, request, pk):
        ressource = get_object_or_404(Resource, pk=pk, statut=PublicationStatus.PUBLIE)

        # Vérifier l'accès
        if ressource.est_gratuit:
            has_access = True
        else:
            has_access = ResourceAccess.objects.filter(eleve=request.user, ressource=ressource).exists()

        if not has_access:
            messages.error(request, "Vous devez acheter cette ressource avant de la télécharger.")
            return redirect("marketplace:detail", pk=ressource.pk)

        # Enregistrer le téléchargement
        Download.objects.create(eleve=request.user, ressource=ressource, created_by=request.user)
        ressource.nombre_telechargements += 1
        ressource.save(update_fields=["nombre_telechargements"])

        # Servir le fichier
        from django.http import FileResponse
        response = FileResponse(ressource.fichier.open(), as_attachment=True, filename=ressource.fichier.name.split("/")[-1])
        return response
