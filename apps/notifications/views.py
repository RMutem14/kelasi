"""
Vues de l'application notifications.

Liste, marquage des notifications, et envoi de notifications système (admin).
"""
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import ListView

from apps.accounts.enums import UserRole
from apps.accounts.models import User
from apps.core.constants import NotificationLevel
from apps.core.mixins import RoleRequiredMixin
from apps.notifications.models import Notification


class NotificationListView(RoleRequiredMixin, ListView):
    """Liste des notifications de l'utilisateur connecté."""
    model = Notification
    template_name = "pages/notifications/index.html"
    context_object_name = "notifications"
    allowed_roles = [UserRole.ADMIN, UserRole.ENSEIGNANT, UserRole.DIRECTEUR_ETUDES, UserRole.ELEVE]

    def get_queryset(self):
        return Notification.objects.filter(destinataire=self.request.user).order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Notifications"
        ctx["page_subtitle"] = "Vos notifications et alertes."
        ctx["non_lues"] = Notification.objects.filter(destinataire=self.request.user, lu=False).count()
        return ctx


class NotificationMarkReadView(RoleRequiredMixin, View):
    """Marque une notification comme lue (via HTMX ou redirect)."""
    allowed_roles = [UserRole.ADMIN, UserRole.ENSEIGNANT, UserRole.DIRECTEUR_ETUDES, UserRole.ELEVE]

    def post(self, request, pk):
        notif = Notification.objects.filter(pk=pk, destinataire=request.user).first()
        if notif:
            notif.lu = True
            notif.save(update_fields=["lu"])
        if request.headers.get("HX-Request") == "true":
            non_lues = Notification.objects.filter(destinataire=request.user, lu=False).count()
            return render(request, "pages/notifications/_notification_item.html", {
                "notif": notif,
                "non_lues": non_lues,
            })
        if notif and notif.url:
            return redirect(notif.url)
        return redirect("notifications:list")


class NotificationMarkAllReadView(RoleRequiredMixin, View):
    """Marque toutes les notifications comme lues."""
    allowed_roles = [UserRole.ADMIN, UserRole.ENSEIGNANT, UserRole.DIRECTEUR_ETUDES, UserRole.ELEVE]

    def post(self, request):
        Notification.objects.filter(destinataire=request.user, lu=False).update(lu=True)
        if request.headers.get("HX-Request") == "true":
            notifications = Notification.objects.filter(destinataire=request.user).order_by("-created_at")
            return render(request, "pages/notifications/_notification_list.html", {
                "notifications": notifications,
                "non_lues": 0,
            })
        return redirect("notifications:list")


class NotificationSendView(RoleRequiredMixin, View):
    """Admin envoie une notification système à un groupe d'utilisateurs."""
    allowed_roles = [UserRole.ADMIN]
    template_name = "pages/notifications/send.html"

    def get(self, request):
        ctx = {
            "page_title": "Envoyer une notification",
            "page_subtitle": "Communiquez avec les utilisateurs de la plateforme.",
            "role_choices": UserRole.choices,
            "niveau_choices": NotificationLevel.choices,
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        titre = request.POST.get("titre", "").strip()
        message = request.POST.get("message", "").strip()
        niveau = request.POST.get("niveau", NotificationLevel.INFO)
        cible = request.POST.get("cible", "all")
        url = request.POST.get("url", "").strip()

        if not titre or not message:
            messages.error(request, "Titre et message sont obligatoires.")
            return redirect("notifications:send")

        # Déterminer les destinataires
        if cible == "all":
            destinataires = User.objects.filter(is_active=True)
        elif cible == "admins":
            destinataires = User.objects.filter(role=UserRole.ADMIN, is_active=True)
        elif cible == "enseignants":
            destinataires = User.objects.filter(role=UserRole.ENSEIGNANT, is_active=True)
        elif cible == "directeurs":
            destinataires = User.objects.filter(role=UserRole.DIRECTEUR_ETUDES, is_active=True)
        elif cible == "eleves":
            destinataires = User.objects.filter(role=UserRole.ELEVE, is_active=True)
        else:
            destinataires = User.objects.filter(is_active=True)

        count = 0
        for user in destinataires:
            Notification.objects.create(
                destinataire=user,
                titre=titre,
                message=message,
                niveau=niveau,
                url=url,
                created_by=request.user,
            )
            count += 1

        messages.success(request, f"Notification envoyée à {count} utilisateur(s).")
        return redirect("notifications:list")
