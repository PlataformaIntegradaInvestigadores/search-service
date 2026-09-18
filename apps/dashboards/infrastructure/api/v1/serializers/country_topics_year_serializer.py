from rest_framework_mongoengine.serializers import DocumentSerializer

from apps.dashboards.domain.entities.country_topics_year import CountryTopicsYear


class CountryTopicsYearSerializer(DocumentSerializer):
    class Meta:
        model = CountryTopicsYear
        fields = "__all__"
