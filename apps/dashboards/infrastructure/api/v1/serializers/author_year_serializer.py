from rest_framework_mongoengine.serializers import DocumentSerializer

from apps.dashboards.domain.entities.author_year import AuthorYear


class AuthorYearSerializer(DocumentSerializer):
    class Meta:
        model = AuthorYear
        fields = "__all__"
