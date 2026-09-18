from rest_framework_mongoengine.serializers import DocumentSerializer

from apps.dashboards.domain.entities.affiliation_topics_year import (
    AffiliationTopicsYear,
)


class AffiliationTopicYearSerializer(DocumentSerializer):
    class Meta:
        model = AffiliationTopicsYear
        fields = "__all__"
