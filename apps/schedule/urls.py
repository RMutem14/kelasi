"""URLs de l'application schedule."""
from django.urls import path

from .views import (
    CreneauConflitCheckView,
    CreneauCreateView,
    CreneauDeleteView,
    ScheduleView,
)

app_name = "schedule"

urlpatterns = [
    path("", ScheduleView.as_view(), name="timetable"),
    path("creer/", CreneauCreateView.as_view(), name="creneau_create"),
    path("conflit/", CreneauConflitCheckView.as_view(), name="conflit_check"),
    path("<uuid:pk>/supprimer/", CreneauDeleteView.as_view(), name="creneau_delete"),
]
