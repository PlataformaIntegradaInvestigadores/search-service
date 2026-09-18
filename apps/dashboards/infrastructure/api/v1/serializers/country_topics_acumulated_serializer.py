from rest_framework_mongoengine.serializers import DocumentSerializer

from apps.dashboards.domain.entities.country_topics_acumulated import (
    CountryTopicsAcumulated,
)


class CountryTopicsAcumulatedSerializer(DocumentSerializer):
    class Meta:
        model = CountryTopicsAcumulated
        fields = "__all__"
