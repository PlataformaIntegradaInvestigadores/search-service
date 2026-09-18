from rest_framework.routers import DefaultRouter

from apps.scopus_integration.infrastructure.api.v1.views.dashboard_information_views import (
    DashboardInformationViewSet,
)

router = DefaultRouter()
router.register(
    "information", DashboardInformationViewSet, basename="dashboard-information"
)
urlpatterns = router.urls
