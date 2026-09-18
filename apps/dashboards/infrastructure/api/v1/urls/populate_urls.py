from django.urls import path

from apps.dashboards.infrastructure.api.v1.views.populate_view import PopulateView

urlpatterns = [
    path("", PopulateView.as_view(), name="populate-dashboard"),
]
