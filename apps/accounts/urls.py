"""URLs de l'application accounts."""
from django.urls import path

from .views import (
    LoginView, logout_view,
    UserListView, UserDetailView, UserCreateView, UserEditView, UserDeleteView,
)

app_name = "accounts"

urlpatterns = [
    # Auth
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    # Admin users CRUD
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/<uuid:pk>/", UserDetailView.as_view(), name="user_detail"),
    path("users/ajouter/", UserCreateView.as_view(), name="user_add"),
    path("users/<uuid:pk>/modifier/", UserEditView.as_view(), name="user_edit"),
    path("users/<uuid:pk>/supprimer/", UserDeleteView.as_view(), name="user_delete"),
]
