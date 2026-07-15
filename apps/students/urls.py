"""URLs de l'application students."""
from django.urls import path

from .views import MyNotesView, MyResourcesView

app_name = "students"

urlpatterns = [
    path("notes/", MyNotesView.as_view(), name="notes"),
    path("ressources/", MyResourcesView.as_view(), name="resources"),
]
