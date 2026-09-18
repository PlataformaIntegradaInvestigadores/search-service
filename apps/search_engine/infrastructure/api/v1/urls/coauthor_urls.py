from rest_framework.routers import DefaultRouter

from apps.search_engine.infrastructure.api.v1.views.coauthor_views import (
    CoAuthorsViewSet,
)

router = DefaultRouter()
router.register(r"", CoAuthorsViewSet, basename="coauthors")
urlpatterns = router.urls
