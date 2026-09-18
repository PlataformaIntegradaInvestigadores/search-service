import uuid
from unittest.mock import Mock

from django.test import RequestFactory, TestCase

from apps.search_engine.domain.entities.affiliation import Affiliation
from apps.search_engine.domain.entities.article import Article
from apps.search_engine.domain.entities.author import Author
from apps.search_engine.infrastructure.api.v1.serializers.affiliation_serializers import (
    AffiliationNameSerializer,
    AffiliationSerializer,
)
from apps.search_engine.infrastructure.api.v1.serializers.article_serializers import (
    ArticleSerializer,
    MostRelevantArticleResponseSerializer,
)
from apps.search_engine.infrastructure.api.v1.serializers.author_serializers import (
    AuthorSerializer,
    RetrieveAuthorSerializer,
)
from apps.search_engine.infrastructure.api.v1.serializers.topic_serializer import (
    TopicSerializer,
)
from apps.search_engine.infrastructure.api.v1.utils.build_paginator import (
    build_pagination_urls,
)


def uid():
    return uuid.uuid4().hex[:12]


class ArticleSerializerTests(TestCase):
    def test_serializes_article_with_relations(self):
        article = Article(
            scopus_id=uid(),
            title="T",
            abstract="A",
            doi="10.1/x",
            publication_date="2024-01-01",
            author_count=0,
            affiliation_count=0,
            corpus="c",
        ).save()
        aff = Affiliation(scopus_id=uid(), name=f"Uni {uid()}").save()
        article.affiliations.connect(aff)
        data = ArticleSerializer(article).data
        self.assertEqual(data["title"], "T")
        self.assertEqual(data["affiliations"], [aff.name])
        self.assertEqual(data["topics"], [])


class MostRelevantArticleResponseSerializerTests(TestCase):
    def test_clamps_negative_counts_to_zero(self):
        data = MostRelevantArticleResponseSerializer(
            {
                "title": "T",
                "author_count": -3,
                "affiliation_count": -1,
                "publication_date": "2024",
                "scopus_id": "1",
                "relevance": 0.5,
            }
        ).data
        self.assertEqual(data["author_count"], 0)
        self.assertEqual(data["affiliation_count"], 0)


class AuthorSerializerTests(TestCase):
    def test_serializes_author_relations(self):
        author = Author(
            scopus_id=uid(),
            first_name="Ana",
            last_name="Perez",
            auth_name="Perez A.",
            initials="A.",
            citation_count=3,
            current_affiliation="Uni X",
        ).save()
        data = AuthorSerializer(author).data
        self.assertEqual(data["first_name"], "Ana")
        self.assertEqual(data["co_authors"], [])
        self.assertEqual(data["articles"], 0)


class RetrieveAuthorSerializerTests(TestCase):
    def test_combines_name_and_counts(self):
        author = Author(
            scopus_id=uid(),
            first_name="Ana",
            last_name="Perez",
            current_affiliation="Uni X",
            citation_count=1,
            updated=True,
        ).save()
        data = RetrieveAuthorSerializer(author).data
        self.assertEqual(data["name"], "Ana Perez")
        self.assertEqual(data["affiliations"], 0)
        self.assertEqual(data["articles"], 0)
        self.assertEqual(data["topics"], 0)


class AffiliationSerializerTests(TestCase):
    def test_serializes_basic_fields(self):
        aff = Affiliation(
            scopus_id=uid(), name="Uni", city="Bogota", country="Colombia"
        ).save()
        data = AffiliationSerializer(aff).data
        self.assertEqual(data["city"], "Bogota")


class AffiliationNameSerializerTests(TestCase):
    def test_renames_scopus_id_to_camel_case(self):
        aff = Affiliation(scopus_id="123", name="Uni").save()
        data = AffiliationNameSerializer(aff).data
        self.assertEqual(data["scopusId"], "123")
        self.assertNotIn("scopus_id", data)

    def test_to_internal_value_maps_back(self):
        serializer = AffiliationNameSerializer(data={"scopusId": "9", "name": "Uni"})
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.validated_data["scopus_id"], "9")


class TopicSerializerTests(TestCase):
    def test_serializes_name(self):
        data = TopicSerializer({"name": "ai"}).data
        self.assertEqual(data["name"], "ai")


class BuildPaginatorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_no_next_page_when_less_than_page_size(self):
        request = self.factory.get("/x")
        info = build_pagination_urls(request, 1, 10, ["a", "b"])
        self.assertIsNone(info["next_page"])
        self.assertIsNone(info["previous_page"])
        self.assertFalse(info["has_more_items"])

    def test_next_page_when_full_page(self):
        request = self.factory.get("/x")
        info = build_pagination_urls(request, 1, 2, ["a", "b"])
        self.assertIsNotNone(info["next_page"])
        self.assertIn("page=2", info["next_page"])
        self.assertTrue(info["has_more_items"])

    def test_previous_page_when_not_first_page(self):
        request = self.factory.get("/x")
        info = build_pagination_urls(request, 3, 10, ["a"])
        self.assertIn("page=2", info["previous_page"])
