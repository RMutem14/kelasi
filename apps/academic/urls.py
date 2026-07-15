"""URLs de l'application academic."""
from django.urls import path

from .views import (
    ClasseListView, ClasseDetailView, ClasseCreateView, ClasseEditView, ClasseDeleteView,
    CoursListView, CoursDetailView, CoursCreateView, CoursEditView, CoursDeleteView,
    EvaluationListView, EvaluationCreateView, EvaluationEditView, EvaluationDeleteView,
)

app_name = "academic"

urlpatterns = [
    # Classes
    path("classes/", ClasseListView.as_view(), name="classe_list"),
    path("classes/ajouter/", ClasseCreateView.as_view(), name="classe_add"),
    path("classes/<uuid:pk>/", ClasseDetailView.as_view(), name="classe_detail"),
    path("classes/<uuid:pk>/modifier/", ClasseEditView.as_view(), name="classe_edit"),
    path("classes/<uuid:pk>/supprimer/", ClasseDeleteView.as_view(), name="classe_delete"),
    # Cours
    path("cours/", CoursListView.as_view(), name="cours_list"),
    path("cours/ajouter/", CoursCreateView.as_view(), name="cours_add"),
    path("cours/<uuid:pk>/", CoursDetailView.as_view(), name="cours_detail"),
    path("cours/<uuid:pk>/modifier/", CoursEditView.as_view(), name="cours_edit"),
    path("cours/<uuid:pk>/supprimer/", CoursDeleteView.as_view(), name="cours_delete"),
    # Évaluations
    path("evaluations/", EvaluationListView.as_view(), name="evaluation_list"),
    path("evaluations/ajouter/", EvaluationCreateView.as_view(), name="evaluation_add"),
    path("evaluations/<uuid:pk>/modifier/", EvaluationEditView.as_view(), name="evaluation_edit"),
    path("evaluations/<uuid:pk>/supprimer/", EvaluationDeleteView.as_view(), name="evaluation_delete"),
]
