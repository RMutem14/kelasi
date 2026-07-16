"""URLs de l'application parents."""
from django.urls import path

from .views import (
    ChildBulletinsView,
    ChildNotesView,
    LinkChildView,
    ParentChildrenView,
    ParentDashboardView,
    UnlinkChildView,
)

app_name = "parents"

urlpatterns = [
    path("", ParentDashboardView.as_view(), name="dashboard"),
    path("enfants/", ParentChildrenView.as_view(), name="children"),
    path("lier/", LinkChildView.as_view(), name="link_child"),
    path("delier/<uuid:pk>/", UnlinkChildView.as_view(), name="unlink_child"),
    path("enfant/<uuid:eleve_pk>/bulletins/", ChildBulletinsView.as_view(), name="child_bulletins"),
    path("enfant/<uuid:eleve_pk>/notes/", ChildNotesView.as_view(), name="child_notes"),
]
