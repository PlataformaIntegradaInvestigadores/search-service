from rest_framework_mongoengine.serializers import DocumentSerializer

from apps.dashboards.domain.entities.province import Province


class ProvinceSerializer(DocumentSerializer):
    class Meta:
        model = Province
        fields = "__all__"
