"""
Mixins de vue réutilisables.

``RoleRequiredMixin`` restreint l'accès à une vue selon le rôle
de l'utilisateur connecté. À combiner avec ``LoginRequiredMixin``.

``HTMXMixin`` facilite le rendu partiel quand la requête est HTMX
(en-tête ``HX-Request: true``).
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.template.loader import select_template
from django.views.generic import View


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin qui restreint l'accès à un ou plusieurs rôles.

    Usage :

        class DashboardDirecteurView(RoleRequiredMixin, TemplateView):
            allowed_roles = [UserRole.DIRECTEUR_ETUDES]
            template_name = "pages/dashboard/directeur.html"
    """

    allowed_roles: list = []

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()
        if self.allowed_roles and user.role not in self.allowed_roles:
            raise PermissionDenied(
                "Votre rôle ne vous permet pas d'accéder à cette page."
            )
        return super().dispatch(request, *args, **kwargs)


class HTMXMixin:
    """
    Mixin qui détecte les requêtes HTMX et permet un rendu partiel.

    Usage :

        class MaView(HTMXMixin, TemplateView):
            template_name = "pages/ma_view.html"
            partial_template_name = "partials/ma_view_content.html"

            def get_template_names(self):
                if self.is_htmx_request():
                    return [self.partial_template_name]
                return super().get_template_names()
    """

    partial_template_name: str | None = None

    def is_htmx_request(self) -> bool:
        """Détecte si la requête courante provient d'HTMX."""
        request: HttpRequest = getattr(self, "request", None)
        if request is None:
            return False
        return request.headers.get("HX-Request", "false").lower() == "true"

    def get_template_names(self) -> list[str]:
        if self.is_htmx_request() and self.partial_template_name:
            return [self.partial_template_name]
        return super().get_template_names()  # type: ignore[misc]
