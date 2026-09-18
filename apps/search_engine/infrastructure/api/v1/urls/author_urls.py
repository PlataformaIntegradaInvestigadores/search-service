from rest_framework.routers import DefaultRouter

from apps.search_engine.infrastructure.api.v1.views.author_views import AuthorViews

router = DefaultRouter()
router.register(r"", AuthorViews, basename="author")
urlpatterns = router.urls
