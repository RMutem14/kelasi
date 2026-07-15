"""URLs de l'application dashboard."""
from django.urls import path

from .views import (
    DashboardHomeView, DesignSystemView, RolesView,
    ProfileView, SettingsView, DirecteurStatsView,
)

app_name = "dashboard"

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="home"),
    path("profil/", ProfileView.as_view(), name="profile"),
    path("parametres/", SettingsView.as_view(), name="settings"),
    path("statistiques/", DirecteurStatsView.as_view(), name="stats"),
    path("design-system/", DesignSystemView.as_view(), name="design_system"),
    path("roles/", RolesView.as_view(), name="roles"),
]
