from django.urls import path

from apps.dashboards.infrastructure.api.v1.views.fairness_views import (
    FairnessBaselineView,
    FairnessMitigationView,
    FairnessSensitivityView,
    FairnessSummaryView,
)

urlpatterns = [
    path("summary/", FairnessSummaryView.as_view(), name="fairness-summary"),
    path("baseline/", FairnessBaselineView.as_view(), name="fairness-baseline"),
    path("mitigation/", FairnessMitigationView.as_view(), name="fairness-mitigation"),
    path(
        "sensitivity/", FairnessSensitivityView.as_view(), name="fairness-sensitivity"
    ),
]
