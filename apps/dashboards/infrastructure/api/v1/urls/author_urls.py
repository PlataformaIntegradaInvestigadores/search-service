from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.dashboards.infrastructure.api.v1.views.author_views import AuthorViews

router = DefaultRouter()
router.register(r"", AuthorViews, basename="author-dashboard")
urlpatterns = [path("", include(router.urls))]
