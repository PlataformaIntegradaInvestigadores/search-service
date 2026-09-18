from rest_framework_mongoengine.serializers import DocumentSerializer

from apps.dashboards.domain.entities.country_topics import CountryTopics


class CountryTopicsSerializer(DocumentSerializer):
    class Meta:
        model = CountryTopics
        fields = "__all__"
