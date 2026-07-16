"""
Vues du portefeuille numérique enseignant et des demandes de retrait.
"""
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import ListView

from apps.accounts.enums import UserRole
from apps.core.mixins import RoleRequiredMixin
from apps.marketplace.models_wallet import Wallet, WithdrawalRequest
from apps.core.utils import normalize_drc_phone


class WalletView(RoleRequiredMixin, View):
    """Page du portefeuille de l'enseignant connecté."""
    allowed_roles = [UserRole.ENSEIGNANT]
    template_name = "pages/marketplace/wallet.html"

    def get(self, request):
        wallet, created = Wallet.objects.get_or_create(
            enseignant=request.user,
            defaults={"created_by": request.user},
        )
        transactions = wallet.transactions.select_related("order", "order__ressource").all()[:20]
        demandes = WithdrawalRequest.objects.filter(enseignant=request.user)[:5]

        ctx = {
            "wallet": wallet,
            "transactions": transactions,
            "demandes": demandes,
            "page_title": "Mon portefeuille",
            "page_subtitle": f"Solde : {wallet.solde} $ — Gérez vos gains et retraits.",
        }
        return render(request, self.template_name, ctx)


class WithdrawalRequestView(RoleRequiredMixin, View):
    """Formulaire de demande de retrait."""
    allowed_roles = [UserRole.ENSEIGNANT]
    template_name = "pages/marketplace/withdrawal_request.html"

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(
            enseignant=request.user,
            defaults={"created_by": request.user},
        )
        ctx = {
            "wallet": wallet,
            "operateur_choices": WithdrawalRequest.Operateur.choices,
            "page_title": "Demander un retrait",
            "page_subtitle": f"Solde disponible : {wallet.solde} $",
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        wallet, _ = Wallet.objects.get_or_create(
            enseignant=request.user,
            defaults={"created_by": request.user},
        )

        montant_str = request.POST.get("montant", "").strip()
        operateur = request.POST.get("operateur", "")
        choix_numero = request.POST.get("choix_numero", "compte")
        numero_telephone = request.POST.get("numero_telephone", "").strip()

        # Validation du montant
        try:
            montant = Decimal(montant_str)
        except Exception:
            messages.error(request, "Montant invalide.")
            return redirect("marketplace:withdrawal_request")

        if montant <= 0:
            messages.error(request, "Le montant doit être supérieur à 0.")
            return redirect("marketplace:withdrawal_request")

        if montant > wallet.solde:
            messages.error(request, f"Solde insuffisant. Votre solde est de {wallet.solde} $.")
            return redirect("marketplace:withdrawal_request")

        # Déterminer le numéro de téléphone
        if choix_numero == "compte":
            numero = normalize_drc_phone(request.user.phone)
            if not numero:
                messages.error(request, "Vous n'avez pas de numéro de téléphone dans votre profil. Choisissez 'Autre numéro'.")
                return redirect("marketplace:withdrawal_request")
            utilise_compte = True
        else:
            numero = normalize_drc_phone(numero_telephone)
            if not numero or len(numero) < 12:
                messages.error(request, "Veuillez saisir un numéro de téléphone valide.")
                return redirect("marketplace:withdrawal_request")
            utilise_compte = False

        if not operateur:
            messages.error(request, "Veuillez choisir un opérateur.")
            return redirect("marketplace:withdrawal_request")

        # Vérification de la correspondance opérateur/numéro
        # Format attendu après normalisation : +243XXXXXXXXX
        if len(numero) >= 13:
            # Après normalisation le 0 initial est retiré : +243812345678
            # On reconstitue le préfixe local (ex: "081") à partir des 2 chiffres après +243
            prefix = "0" + numero[4:6]
            
            if operateur == WithdrawalRequest.Operateur.ORANGE:
                valid_prefixes = {"084", "085","089", "080"}
                if prefix not in valid_prefixes:
                    messages.error(request, f"Le numéro {numero} n'est pas un numéro Orange Money valide. Préfixes acceptés : {', '.join(valid_prefixes)}")
                    return redirect("marketplace:withdrawal_request")

            elif operateur == WithdrawalRequest.Operateur.AIRTEL:
                valid_prefixes = {"097", "098", "099", "090", "096"}
                if prefix not in valid_prefixes:
                    messages.error(request, f"Le numéro {numero} n'est pas un numéro Airtel Money valide. Préfixes acceptés : {', '.join(valid_prefixes)}")
                    return redirect("marketplace:withdrawal_request")
            
            elif operateur == WithdrawalRequest.Operateur.VODACOM:
                valid_prefixes = {"081", "082"}
                if prefix not in valid_prefixes:
                    messages.error(request, f"Le numéro {numero} n'est pas un numéro Vodacom M-Pesa valide. Préfixes acceptés : {', '.join(valid_prefixes)}")
                    return redirect("marketplace:withdrawal_request")

        # Créer la demande
        demande = WithdrawalRequest.objects.create(
            enseignant=request.user,
            montant=montant,
            operateur=operateur,
            numero_telephone=numero,
            utilise_numero_compte=utilise_compte,
            created_by=request.user,
        )

        # Débiter immédiatement le wallet (le montant est bloqué)
        wallet.debiter(montant, description=f"Retrait demandé via {operateur} ({numero})")
        # Lier la transaction de débit à la demande
        last_tx = wallet.transactions.first()
        if last_tx:
            last_tx.description = f"Retrait #{str(demande.pk)[:8]} — {operateur}"
            last_tx.save(update_fields=["description"])

        # Envoyer l'email aux admins
        self._notify_admins(request, demande)

        messages.success(request, f"Demande de retrait de {montant} $ créée. Vous serez notifié du traitement.")
        return redirect("marketplace:wallet")

    def _notify_admins(self, request, demande):
        """Envoie un email aux administrateurs avec les infos de la demande."""
        from apps.core.email import get_email_service, EmailMessage
        from apps.accounts.models import User

        admins = User.objects.filter(role=UserRole.ADMIN, is_active=True)
        admin_emails = [a.email for a in admins]
        if not admin_emails:
            admin_emails = ["admin@elikya.cd"]

        body = f"""
NOUVELLE DEMANDE DE RETRAIT — Huduma|Kelasi
============================================

Enseignant : {demande.enseignant.full_name}
Email : {demande.enseignant.email}
Téléphone du compte : {demande.enseignant.phone or 'Non renseigné'}

Montant demandé : {demande.montant} $
Opérateur : {demande.get_operateur_display()}
Numéro de transfert : {demande.numero_telephone}
Utilise le numéro du compte : {'Oui' if demande.utilise_numero_compte else 'Non'}

Date de la demande : {demande.created_at.strftime('%d/%m/%Y à %H:%M')}
Référence : {str(demande.pk)[:8]}

ACTION REQUISE :
1. Connectez-vous à l'admin Django
2. Traitez la demande dans Marketplace > Demandes de retrait
3. Effectuez le transfert via l'opérateur choisi
4. Marquez la demande comme 'Payée'

Cet email a été envoyé automatiquement par la plateforme Huduma|Kelasi.
"""

        html_body = f"""
<h2 style="color: #4F46E5;">Nouvelle demande de retrait</h2>
<table style="border-collapse: collapse; width: 100%;">
<tr><td style="padding: 8px; border: 1px solid #E2E8F0; font-weight: bold;">Enseignant</td><td style="padding: 8px; border: 1px solid #E2E8F0;">{demande.enseignant.full_name}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #E2E8F0; font-weight: bold;">Email</td><td style="padding: 8px; border: 1px solid #E2E8F0;">{demande.enseignant.email}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #E2E8F0; font-weight: bold;">Montant</td><td style="padding: 8px; border: 1px solid #E2E8F0; color: #10B981; font-weight: bold;">{demande.montant} $</td></tr>
<tr><td style="padding: 8px; border: 1px solid #E2E8F0; font-weight: bold;">Opérateur</td><td style="padding: 8px; border: 1px solid #E2E8F0;">{demande.get_operateur_display()}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #E2E8F0; font-weight: bold;">Numéro</td><td style="padding: 8px; border: 1px solid #E2E8F0;">{demande.numero_telephone}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #E2E8F0; font-weight: bold;">Date</td><td style="padding: 8px; border: 1px solid #E2E8F0;">{demande.created_at.strftime('%d/%m/%Y à %H:%M')}</td></tr>
</table>
<p style="color: #64748B; margin-top: 16px;">Connectez-vous à l'admin pour traiter cette demande.</p>
"""

        service = get_email_service()
        service.send(EmailMessage(
            to=admin_emails,
            subject=f"[Huduma] Demande de retrait — {demande.enseignant.full_name} — {demande.montant} $",
            body=body,
            html_body=html_body,
            from_email="noreply@elikya.cd",
            from_name="Huduma|Kelasi",
        ))


class WithdrawalListView(RoleRequiredMixin, ListView):
    """Historique des demandes de retrait de l'enseignant."""
    model = WithdrawalRequest
    template_name = "pages/marketplace/withdrawal_list.html"
    context_object_name = "demandes"
    allowed_roles = [UserRole.ENSEIGNANT]

    def get_queryset(self):
        return WithdrawalRequest.objects.filter(enseignant=self.request.user).order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Mes demandes de retrait"
        ctx["page_subtitle"] = "Historique de toutes vos demandes."
        return ctx
