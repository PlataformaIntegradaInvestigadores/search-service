from rest_framework_mongoengine.serializers import DocumentSerializer

from apps.dashboards.domain.entities.affiliation_year_acumulated import (
    AffiliationAcumulated,
)


class AffiliationAcumulatedSerializer(DocumentSerializer):
    class Meta:
        model = AffiliationAcumulated
        fields = "__all__"
