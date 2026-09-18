from rest_framework_mongoengine.serializers import DocumentSerializer

from apps.dashboards.domain.entities.affiliation_topics import AffiliationTopics


class AffiliationTopicsSerializer(DocumentSerializer):
    class Meta:
        model = AffiliationTopics
        fields = "__all__"
