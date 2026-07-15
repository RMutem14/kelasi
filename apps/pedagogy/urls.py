"""URLs de l'application pedagogy."""
from django.urls import path

from .views import (
    DocumentListView, DocumentDetailView,
    DocumentCreateView, DocumentEditView, DocumentDeleteView,
)

app_name = "pedagogy"

urlpatterns = [
    path("", DocumentListView.as_view(), name="document_list"),
    path("ajouter/", DocumentCreateView.as_view(), name="document_add"),
    path("<uuid:pk>/", DocumentDetailView.as_view(), name="document_detail"),
    path("<uuid:pk>/modifier/", DocumentEditView.as_view(), name="document_edit"),
    path("<uuid:pk>/supprimer/", DocumentDeleteView.as_view(), name="document_delete"),
]
