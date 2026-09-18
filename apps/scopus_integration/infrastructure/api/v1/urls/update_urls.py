from rest_framework.routers import DefaultRouter

from apps.scopus_integration.infrastructure.api.v1.views.update_information_views import (
    UpdateInformationViewSet,
)

router = DefaultRouter()
router.register("update", UpdateInformationViewSet, basename="update-information")
urlpatterns = router.urls
