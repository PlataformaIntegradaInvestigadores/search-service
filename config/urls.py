"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from config.health import health_check

urlpatterns = [
    path("health/", health_check),
    path("api-se/admin/", admin.site.urls),
    path("api-se/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI for schema:
    path(
        "api-se/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api-se/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),  # Urls for each app
    path(
        "api-se/v1/",
        include("apps.search_engine.infrastructure.api.v1.urls.root_urls"),
        name="author",
    ),
    path(
        "api-se/v1/",
        include("apps.scopus_integration.infrastructure.api.v1.urls.root_url"),
        name="scopus",
    ),
    path(
        "api-se/v1/dashboard/",
        include("apps.dashboards.infrastructure.api.v1.urls.root_urls"),
        name="dashboard",
    ),
    path(
        "api-se/v1/text-processing/",
        include("apps.text_processing.infrastructure.api.urls"),
        name="text_processing",
    ),
    path(
        "api-se/v1/auth/",
        include("apps.authentication.infrastructure.api.v1.urls.root_urls"),
        name="authentication",
    ),
]
