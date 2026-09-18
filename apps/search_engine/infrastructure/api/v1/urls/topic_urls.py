from rest_framework.routers import DefaultRouter

from apps.search_engine.infrastructure.api.v1.views.topic_views import TopicViewSet

router = DefaultRouter()
router.register(r"", TopicViewSet, basename="article")
urlpatterns = [] + router.urls
