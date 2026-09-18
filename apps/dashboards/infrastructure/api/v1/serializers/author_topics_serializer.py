from rest_framework_mongoengine.serializers import DocumentSerializer

from apps.dashboards.domain.entities.author_topics import AuthorTopics


class AuthorTopicsSerializer(DocumentSerializer):
    class Meta:
        model = AuthorTopics
        fields = "__all__"
