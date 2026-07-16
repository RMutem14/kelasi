"""URLs de l'application attendance."""
from django.urls import path

from .views import (
    AttendanceHistoryView,
    AttendanceSaisieView,
    AttendanceSaveView,
    ChildAttendanceView,
    MyAttendanceView,
)

app_name = "attendance"

urlpatterns = [
    path("saisie/", AttendanceSaisieView.as_view(), name="saisie"),
    path("save/", AttendanceSaveView.as_view(), name="save"),
    path("historique/", AttendanceHistoryView.as_view(), name="history"),
    path("mes-presences/", MyAttendanceView.as_view(), name="my_attendance"),
    path("enfant/<uuid:eleve_pk>/", ChildAttendanceView.as_view(), name="child_attendance"),
]
