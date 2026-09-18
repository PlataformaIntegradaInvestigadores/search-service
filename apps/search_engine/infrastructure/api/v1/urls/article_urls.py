from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.search_engine.infrastructure.api.v1.views.article_views import (
    ArticleCount,
    ArticleViewSet,
)

router = DefaultRouter()
router.register(r"", ArticleViewSet, basename="article")
urlpatterns = [
    path("count/", ArticleCount.as_view(), name="article-count"),
] + router.urls
