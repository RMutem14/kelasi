"""URLs de l'application validation."""
from django.urls import path

from .views import (
    DocumentValidationListView, DocumentValidationActionView,
    DirecteurClassesView, DirecteurCoursView,
)

app_name = "validation"

urlpatterns = [
    path("documents/", DocumentValidationListView.as_view(), name="document_list"),
    path("documents/<uuid:pk>/action/", DocumentValidationActionView.as_view(), name="document_action"),
    path("classes/", DirecteurClassesView.as_view(), name="directeur_classes"),
    path("cours/", DirecteurCoursView.as_view(), name="directeur_cours"),
]
