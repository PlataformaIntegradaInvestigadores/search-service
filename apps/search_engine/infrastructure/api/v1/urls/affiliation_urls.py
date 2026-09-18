from rest_framework.routers import DefaultRouter

from apps.search_engine.infrastructure.api.v1.views.affiliation_views import (
    AffiliationViewSet,
)

router = DefaultRouter()
router.register(r"", AffiliationViewSet, basename="affiliation")
urlpatterns = [] + router.urls
