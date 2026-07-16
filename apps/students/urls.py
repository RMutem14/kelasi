"""URLs de l'application students."""
from django.urls import path

from .views import (
    BulletinGenerateView,
    BulletinListView,
    BulletinPDFView,
    BulletinPDFViewerView,
    BulletinPublishAllView,
    BulletinPublishView,
    MyBulletinsView,
    MyNotesView,
    MyResourcesView,
    PeriodeCreateView,
    PeriodeListView,
)

app_name = "students"

urlpatterns = [
    path("notes/", MyNotesView.as_view(), name="notes"),
    path("ressources/", MyResourcesView.as_view(), name="resources"),
    # Bulletins — élève
    path("bulletins/", MyBulletinsView.as_view(), name="my_bulletins"),
    path("bulletins/<uuid:pk>/pdf/", BulletinPDFView.as_view(), name="bulletin_pdf"),
    path("bulletins/<uuid:pk>/visualiser/", BulletinPDFViewerView.as_view(), name="bulletin_viewer"),
    # Bulletins — admin/directeur
    path("admin/bulletins/", BulletinListView.as_view(), name="bulletin_list"),
    path("admin/bulletins/generer/", BulletinGenerateView.as_view(), name="bulletin_generate"),
    path("admin/bulletins/<uuid:pk>/publier/", BulletinPublishView.as_view(), name="bulletin_publish"),
    path("admin/bulletins/publier-tout/", BulletinPublishAllView.as_view(), name="bulletin_publish_all"),
    # Périodes
    path("admin/periodes/", PeriodeListView.as_view(), name="periode_list"),
    path("admin/periodes/creer/", PeriodeCreateView.as_view(), name="periode_create"),
]
