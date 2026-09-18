from rest_framework import serializers


class ArticleSerializer(serializers.Serializer):
    title = serializers.CharField()
    abstract = serializers.CharField()
    doi = serializers.CharField()
    publication_date = serializers.CharField()
    author_count = serializers.IntegerField()
    affiliation_count = serializers.IntegerField()
    corpus = serializers.CharField()
    affiliations = serializers.SerializerMethodField()
    topics = serializers.SerializerMethodField()
    scopus_id = serializers.CharField()

    def get_affiliation_count(self, obj):
        return len(obj.affiliations.all())

    def get_affiliations(self, obj):
        return [affiliation.name for affiliation in obj.affiliations.all()]

    def get_topics(self, obj):
        return [topic.name for topic in obj.topics.all()]


class ArticlesByAuthorSerializer(serializers.Serializer):
    title = serializers.CharField()
    publication_date = serializers.CharField()
    scopus_id = serializers.CharField()


class MostRelevantArticlesRequestSerializer(serializers.Serializer):
    query = serializers.CharField()
    page = serializers.IntegerField()
    size = serializers.IntegerField()
    type = serializers.CharField(required=False)
    years = serializers.ListField(child=serializers.CharField(), required=False)


class MostRelevantArticleResponseSerializer(serializers.Serializer):
    title = serializers.CharField()
    author_count = serializers.IntegerField(min_value=0)  # Asegurar que acepte cero
    affiliation_count = serializers.IntegerField(
        min_value=0
    )  # Asegurar que acepte cero
    publication_date = serializers.CharField()
    scopus_id = serializers.CharField()
    relevance = serializers.FloatField()
    authors = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
    affiliations = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Asegurar que los conteos sean enteros positivos
        data["author_count"] = max(0, int(instance.get("author_count", 0)))
        data["affiliation_count"] = max(0, int(instance.get("affiliation_count", 0)))
        return data
