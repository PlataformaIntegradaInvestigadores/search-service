from rest_framework import serializers


class AuthorSerializer(serializers.Serializer):
    scopus_id = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    auth_name = serializers.CharField()
    initials = serializers.CharField()
    affiliations = serializers.SerializerMethodField()
    articles = serializers.SerializerMethodField()
    co_authors = serializers.SerializerMethodField()
    topics = serializers.SerializerMethodField()
    citation_count = serializers.IntegerField()
    current_affiliation = serializers.CharField()

    def get_affiliations(self, obj):
        return [affiliation.name for affiliation in obj.affiliations.all()]

    def get_co_authors(self, obj):
        return [co_author.auth_name for co_author in obj.co_authors.all()]

    def get_articles(self, obj):
        total = [article.title for article in obj.articles.all()]
        return len(total)

    def get_topics(self, obj):
        return [topic.name for topic in obj.topics.all()]


class RetrieveAuthorSerializer(serializers.Serializer):
    scopus_id = serializers.CharField()
    name = serializers.SerializerMethodField()
    affiliations = serializers.SerializerMethodField()
    articles = serializers.SerializerMethodField()
    topics = serializers.SerializerMethodField()
    current_affiliation = serializers.CharField()
    citation_count = serializers.IntegerField()
    updated = serializers.BooleanField()

    def get_name(self, obj):
        return obj.first_name + " " + obj.last_name

    def get_affiliations(self, obj):
        affiliations = [affiliation.name for affiliation in obj.affiliations.all()]
        return len(affiliations)

    def get_articles(self, obj):
        articles = [article.title for article in obj.articles.all()]
        return len(articles)

    def get_topics(self, obj):
        topics = [topic.name for topic in obj.topics.all()]
        return len(topics)


class MostRelevantAuthorsRequestSerializer(serializers.Serializer):
    topic = serializers.CharField()
    authors_number = serializers.IntegerField()
    type = serializers.CharField(required=False, allow_blank=True)
    affiliations = serializers.ListField(
        required=False, child=serializers.CharField(), allow_empty=True
    )


class AuthorCoAuthorSerializer(serializers.Serializer):
    scopus_id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    initials = serializers.CharField()
