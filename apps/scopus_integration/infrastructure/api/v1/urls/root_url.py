from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.scopus_integration.infrastructure.api.v1.views.corpus_modeling_views import (
    GenerateCorpusView,
)
from apps.scopus_integration.infrastructure.api.v1.views.model_generation_views import (
    GenerateModelView,
)
from apps.scopus_integration.infrastructure.api.v1.views.scopus_integration_views import (
    ScopusIntegrationViewSet,
)

router = DefaultRouter()

router.register(
    "scopus-integration", ScopusIntegrationViewSet, basename="scopus-integration"
)
urlpatterns = [
    path(
        "scopus-integration/",
        ScopusIntegrationViewSet.as_view({"get": "list"}),
        name="scopus-integration",
    ),
    path("generate-corpus/", GenerateCorpusView.as_view(), name="generate-corpus"),
    path("generate-model/", GenerateModelView.as_view(), name="generate-model"),
    path(
        "information/",
        include("apps.scopus_integration.infrastructure.api.v1.urls.update_urls"),
        name="update-information",
    ),
    path(
        "dashboard/",
        include(
            "apps.scopus_integration.infrastructure.api.v1.urls.dashboard_information_urls"
        ),
        name="dashboard",
    ),
    path(
        "admin/",
        include("apps.scopus_integration.infrastructure.api.v1.urls.logs_url"),
        name="admin",
    ),
]
