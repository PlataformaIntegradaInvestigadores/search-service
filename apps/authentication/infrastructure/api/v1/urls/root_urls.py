from django.urls import path

from apps.authentication.infrastructure.api.v1.views.login import LoginView
from apps.authentication.infrastructure.api.v1.views.logout import LogoutView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
