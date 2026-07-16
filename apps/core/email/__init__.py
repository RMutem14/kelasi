"""
Couche d'abstraction pour l'envoi d'emails.

Architecture scalable : permet de basculer entre l'affichage console
(pour le MVP/démo) et l'API Brevo (SendinBlue) sans modifier le code métier.

Pour activer Brevo :
1. pip install brevo-python
2. Configurer dans .env :
   EMAIL_BACKEND_PROVIDER=brevo
   BREVO_API_KEY=your-api-key
   BREVO_SENDER_EMAIL=noreply@elikya.cd
   BREVO_SENDER_NAME=Huduma Kelasi
3. Le BrevoEmailService utilisera l'API Brevo automatiquement
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class EmailMessage:
    """Représentation neutre d'un email."""
    to: List[str]
    subject: str
    body: str
    html_body: str = ""
    from_email: str = ""
    from_name: str = ""
    reply_to: List[str] = None
    attachments: List[dict] = None  # [{"filename": "...", "content": b"...", "type": "application/pdf"}]


class EmailService(ABC):
    """Interface abstraite pour tous les fournisseurs d'email."""

    @abstractmethod
    def send(self, message: EmailMessage) -> dict:
        """
        Envoie un email.

        Returns:
            dict avec "success" (bool), "message_id" (str), "error" (str)
        """
        ...

    def send_template(self, *, to: List[str], template_name: str, context: dict) -> dict:
        """
        Envoie un email basé sur un template (optionnel).
        Les implémentations qui supportent les templates (comme Brevo)
        peuvent surcharger cette méthode.
        """
        # Par défaut, on ne fait rien — les implémentations concrètes décident
        return {"success": False, "error": "Templates non supportés par ce fournisseur."}


# ============================================================
# ConsoleEmailService — pour le MVP / démo jury
# ============================================================

class ConsoleEmailService(EmailService):
    """
    Affiche l'email dans la console Django.

    Utilisé par défaut en développement. Aucune configuration requise.
    L'email s'affiche dans le terminal où tourne `python manage.py runserver`.
    """

    name = "console"

    def send(self, message: EmailMessage) -> dict:
        """Affiche l'email formaté dans la console."""
        import textwrap

        separator = "=" * 60
        print(f"\n{separator}")
        print(f"📧 EMAIL — {message.subject}")
        print(separator)
        print(f"De   : {message.from_name} <{message.from_email}>")
        print(f"À    : {', '.join(message.to)}")
        if message.reply_to:
            print(f"Rép. : {', '.join(message.reply_to)}")
        print(separator)
        print(f"\n{message.body}")
        if message.html_body:
            print(f"\n--- Version HTML ({len(message.html_body)} caractères) ---")
        print(f"\n{separator}\n")

        return {"success": True, "message_id": f"console-{id(message)}", "error": ""}


# ============================================================
# BrevoEmailService — pour la production (stub prêt à implémenter)
# ============================================================

class BrevoEmailService(EmailService):
    """
    Envoie des emails via l'API Brevo (SendinBlue).

    Pour activer :
    1. pip install brevo-python
    2. Configurer BREVO_API_KEY dans .env
    3. Configurer EMAIL_BACKEND_PROVIDER=brevo dans .env

    Le SDK Brevo sera importé dynamiquement pour éviter une dépendance
    obligatoire en développement.
    """

    name = "brevo"

    def __init__(self):
        self.api_key = self._get_config("BREVO_API_KEY", "")
        self.sender_email = self._get_config("BREVO_SENDER_EMAIL", "noreply@elikya.cd")
        self.sender_name = self._get_config("BREVO_SENDER_NAME", "Huduma Kelasi")

    def _get_config(self, key, default=""):
        from django.conf import settings
        return getattr(settings, key, default)

    def send(self, message: EmailMessage) -> dict:
        """Envoie via l'API Brevo."""
        try:
            # Import dynamique — brevo-python n'est pas requis en dev
            import brevo_python
            from brevo_python.rest import ApiException
        except ImportError:
            return {
                "success": False,
                "error": "brevo-python n'est pas installé. Lancez : pip install brevo-python",
            }

        try:
            configuration = brevo_python.Configuration()
            configuration.api_key["api-key"] = self.api_key
            api_instance = brevo_python.TransactionalEmailsApi(brevo_python.ApiClient(configuration))

            sender = brevo_python.Sender(
                name=message.from_name or self.sender_name,
                email=message.from_email or self.sender_email,
            )

            to_list = [brevo_python.SendSmtpEmailTo(email=e) for e in message.to]

            smtp_email = brevo_python.SendSmtpEmail(
                sender=sender,
                to=to_list,
                subject=message.subject,
                html_content=message.html_body or f"<p>{message.body}</p>",
                text_content=message.body,
                reply_to=brevo_python.SendSmtpEmailReplyTo(
                    email=message.reply_to[0] if message.reply_to else self.sender_email
                ),
            )

            result = api_instance.send_transac_email(smtp_email)
            return {"success": True, "message_id": result.message_id, "error": ""}

        except ApiException as e:
            return {"success": False, "error": f"Brevo API error: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Erreur inattendue: {e}"}

    def send_template(self, *, to: List[str], template_id: int, params: dict) -> dict:
        """Envoie via un template Brevo (ID numérique)."""
        try:
            import brevo_python
            from brevo_python.rest import ApiException
        except ImportError:
            return {"success": False, "error": "brevo-python n'est pas installé."}

        try:
            configuration = brevo_python.Configuration()
            configuration.api_key["api-key"] = self.api_key
            api_instance = brevo_python.TransactionalEmailsApi(brevo_python.ApiClient(configuration))

            sender = brevo_python.Sender(
                name=self.sender_name,
                email=self.sender_email,
            )
            to_list = [brevo_python.SendSmtpEmailTo(email=e) for e in to]

            smtp_email = brevo_python.SendSmtpEmail(
                sender=sender,
                to=to_list,
                template_id=template_id,
                params=params,
            )

            result = api_instance.send_transac_email(smtp_email)
            return {"success": True, "message_id": result.message_id, "error": ""}

        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# Factory
# ============================================================

_SERVICE_REGISTRY = {
    "console": ConsoleEmailService,
    "brevo": BrevoEmailService,
}

_email_service_instance = None


def get_email_service() -> EmailService:
    """
    Factory : retourne l'instance du service email configuré.

    Déterminé par settings.EMAIL_BACKEND_PROVIDER.
    Par défaut : "console".

    Usage :
        from apps.core.email import get_email_service, EmailMessage
        service = get_email_service()
        service.send(EmailMessage(
            to=["admin@elikya.cd"],
            subject="Nouvelle demande de retrait",
            body="L'enseignant X demande un retrait de 50 $",
            from_email="noreply@elikya.cd",
            from_name="Huduma Kelasi",
        ))
    """
    global _email_service_instance
    if _email_service_instance is not None:
        return _email_service_instance

    from django.conf import settings
    provider = getattr(settings, "EMAIL_BACKEND_PROVIDER", "console")
    service_class = _SERVICE_REGISTRY.get(provider, ConsoleEmailService)
    _email_service_instance = service_class()
    return _email_service_instance
