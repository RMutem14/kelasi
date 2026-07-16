"""URLs de l'application finance."""
from django.urls import path

from .views import (
    FinanceDashboardView,
    FraisAssignView,
    FraisEleveListView,
    FraisElevePaymentView,
    FraisTypeCreateView,
    FraisTypeListView,
    PaiementListView,
)

app_name = "finance"

urlpatterns = [
    path("", FinanceDashboardView.as_view(), name="dashboard"),
    path("types/", FraisTypeListView.as_view(), name="frais_type_list"),
    path("types/creer/", FraisTypeCreateView.as_view(), name="frais_type_create"),
    path("eleves/", FraisEleveListView.as_view(), name="frais_eleve_list"),
    path("eleves/assigner/", FraisAssignView.as_view(), name="frais_assign"),
    path("eleves/<uuid:pk>/payer/", FraisElevePaymentView.as_view(), name="frais_pay"),
    path("paiements/", PaiementListView.as_view(), name="paiement_list"),
]
