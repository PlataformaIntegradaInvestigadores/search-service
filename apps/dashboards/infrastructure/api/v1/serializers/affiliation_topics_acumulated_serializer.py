from rest_framework_mongoengine.serializers import DocumentSerializer

from apps.dashboards.domain.entities.affiliation_topics_acumulated import (
    AffiliationTopicsAcumulated,
)


class AffiliationTopicAcumulatedSerializer(DocumentSerializer):
    class Meta:
        model = AffiliationTopicsAcumulated
        fields = "__all__"
