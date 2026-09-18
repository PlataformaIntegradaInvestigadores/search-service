from rest_framework_mongoengine.serializers import DocumentSerializer

from apps.dashboards.domain.entities.country_year import CountryYear


class CountryYearSerializer(DocumentSerializer):
    class Meta:
        model = CountryYear
        fields = "__all__"
