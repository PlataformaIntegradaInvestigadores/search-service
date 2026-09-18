from rest_framework_mongoengine.serializers import DocumentSerializer

from apps.dashboards.domain.entities.province_year import ProvinceYear


class ProvinceYearSerializer(DocumentSerializer):
    class Meta:
        model = ProvinceYear
        fields = "__all__"
