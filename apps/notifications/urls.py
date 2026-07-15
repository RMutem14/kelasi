"""URLs de l'application notifications."""
from django.urls import path

from .views import (
    NotificationListView, NotificationMarkReadView,
    NotificationMarkAllReadView, NotificationSendView,
)

app_name = "notifications"

urlpatterns = [
    path("", NotificationListView.as_view(), name="list"),
    path("envoyer/", NotificationSendView.as_view(), name="send"),
    path("<uuid:pk>/lu/", NotificationMarkReadView.as_view(), name="mark_read"),
    path("tout-lu/", NotificationMarkAllReadView.as_view(), name="mark_all_read"),
]
