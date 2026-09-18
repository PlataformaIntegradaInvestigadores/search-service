from rest_framework_mongoengine.serializers import DocumentSerializer

from apps.dashboards.domain.entities.country_acumulated import CountryAcumulated


class CountryAcumulatedSerializer(DocumentSerializer):
    class Meta:
        model = CountryAcumulated
        fields = "__all__"
