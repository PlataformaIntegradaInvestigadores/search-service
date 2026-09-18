from rest_framework_mongoengine.serializers import DocumentSerializer

from apps.dashboards.domain.entities.affiliation import Affiliation


class AffiliationSerializer(DocumentSerializer):
    class Meta:
        model = Affiliation
        fields = "__all__"
