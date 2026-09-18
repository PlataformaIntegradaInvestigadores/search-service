from rest_framework.routers import DefaultRouter

from apps.search_engine.infrastructure.api.v1.views.llm_search_views import (
    LLMSearchViewSet,
)

router = DefaultRouter()
router.register("", LLMSearchViewSet, basename="llm-search")
urlpatterns = router.urls
