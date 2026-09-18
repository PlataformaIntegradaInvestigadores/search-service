from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.scopus_integration.infrastructure.api.v1.views.etl_views import EtlRunView
from apps.scopus_integration.infrastructure.api.v1.views.logger_views import (
    LoggerViewSet,
)

router = DefaultRouter()
router.register("logs", LoggerViewSet, basename="logs")

urlpatterns = router.urls + [
    # POST  api-se/v1/admin/etl/run/  → dispara ETL en background, devuelve 202
    # GET   api-se/v1/admin/etl/run/  → polling de estado {status: "running"|"idle"}
    path("etl/run/", EtlRunView.as_view(), name="etl-run"),
]
