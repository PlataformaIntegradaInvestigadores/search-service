from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.dashboards.infrastructure.api.v1.views.province_views import ProvinceViews

router = DefaultRouter()
router.register(r"", ProvinceViews, basename="province-dashboard")
urlpatterns = [path("", include(router.urls))]
