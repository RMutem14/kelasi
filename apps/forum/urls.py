"""URLs de l'application forum."""
from django.urls import path

from .views import (
    QuestionCloseView,
    QuestionCreateView,
    QuestionDetailView,
    QuestionListView,
    ReponseCreateView,
    ReponseValidateView,
)

app_name = "forum"

urlpatterns = [
    path("", QuestionListView.as_view(), name="question_list"),
    path("creer/", QuestionCreateView.as_view(), name="question_create"),
    path("<uuid:pk>/", QuestionDetailView.as_view(), name="question_detail"),
    path("<uuid:pk>/fermer/", QuestionCloseView.as_view(), name="question_close"),
    path("<uuid:pk>/repondre/", ReponseCreateView.as_view(), name="reponse_create"),
    path("reponse/<uuid:pk>/valider/", ReponseValidateView.as_view(), name="reponse_validate"),
]
