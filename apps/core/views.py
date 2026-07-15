"""
Vues transverses de l'application core.

Contient uniquement les handlers d'erreur 403, 404 et 500,
ainsi qu'une vue de statut pour vérifier que le projet démarre.
"""
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse


def error_403(request: HttpRequest, exception=None) -> HttpResponse:
    """Handler 403 : accès interdit."""
    return TemplateResponse(
        request,
        "errors/403.html",
        status=403,
    )


def error_404(request: HttpRequest, exception=None) -> HttpResponse:
    """Handler 404 : page introuvable."""
    return TemplateResponse(
        request,
        "errors/404.html",
        status=404,
    )


def error_500(request: HttpRequest) -> HttpResponse:
    """Handler 500 : erreur serveur."""
    return TemplateResponse(
        request,
        "errors/500.html",
        status=500,
    )
