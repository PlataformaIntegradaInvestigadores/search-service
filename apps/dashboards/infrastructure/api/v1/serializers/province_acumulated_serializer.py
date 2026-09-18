from rest_framework_mongoengine.serializers import DocumentSerializer

from apps.dashboards.domain.entities.province_acumulated import ProvinceAcumulated


class ProvinceAcumulatedSerializer(DocumentSerializer):
    class Meta:
        model = ProvinceAcumulated
        fields = "__all__"
