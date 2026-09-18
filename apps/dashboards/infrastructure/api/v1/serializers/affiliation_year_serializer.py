from rest_framework_mongoengine.serializers import DocumentSerializer

from apps.dashboards.domain.entities.affiliation_year import AffiliationYear


class AffiliationYearSerializer(DocumentSerializer):
    class Meta:
        model = AffiliationYear
        fields = "__all__"
