"""URLs de l'application marketplace."""
from django.urls import path

from .views import (
    CatalogView, ResourceDetailView, ResourceCreateView,
    MyResourcesView, MySalesView, MyPurchasesView,
    BuyView, DownloadView,
)
from .views_wallet import (
    WalletView, WithdrawalRequestView, WithdrawalListView,
)

app_name = "marketplace"

urlpatterns = [
    # Catalogue et ressources
    path("catalogue/", CatalogView.as_view(), name="catalog"),
    path("publier/", ResourceCreateView.as_view(), name="publish"),
    path("mes-ressources/", MyResourcesView.as_view(), name="my_resources"),
    path("mes-ventes/", MySalesView.as_view(), name="my_sales"),
    path("mes-achats/", MyPurchasesView.as_view(), name="my_purchases"),
    path("<uuid:pk>/", ResourceDetailView.as_view(), name="detail"),
    path("<uuid:pk>/acheter/", BuyView.as_view(), name="buy"),
    path("<uuid:pk>/telecharger/", DownloadView.as_view(), name="download"),
    # Portefeuille et retraits
    path("portefeuille/", WalletView.as_view(), name="wallet"),
    path("portefeuille/retrait/", WithdrawalRequestView.as_view(), name="withdrawal_request"),
    path("portefeuille/retraits/", WithdrawalListView.as_view(), name="withdrawal_list"),
]
