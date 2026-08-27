import random
import uuid
from unittest.mock import MagicMock, patch

from django.test import TestCase
from neomodel import db

from apps.search_engine.application.services.affiliation_service import (
    AffiliationService,
)
from apps.search_engine.application.services.article_service import ArticleService
from apps.search_engine.application.services.author_service import AuthorService
from apps.search_engine.application.services.coauthored_service import (
    CoAuthoredService,
)
from apps.search_engine.application.services.topic_service import TopicService
from apps.search_engine.domain.entities.affiliation import Affiliation
from apps.search_engine.domain.entities.article import Article
from apps.search_engine.domain.entities.author import Author
from apps.search_engine.domain.entities.topic import Topic


def uid():
    return uuid.uuid4().hex[:12]


def nid():
    return str(random.randint(10**8, 10**9 - 1))


def make_article(**overrides):
    data = {
        "scopus_id": uid(),
        "title": "T",
        "publication_date": "2024-01-01",
        "abstract": "abs",
        "author_count": 0,
        "affiliation_count": 0,
    }
    data.update(overrides)
    return Article(**data).save()


def make_author(**overrides):
    data = {"scopus_id": uid(), "first_name": "A", "last_name": "B"}
    data.update(overrides)
    return Author(**data).save()


class ArticleServiceTests(TestCase):
    def setUp(self):
        self.service = ArticleService()

    def test_find_by_id(self):
        article = make_article()
        found = self.service.find_by_id(article.scopus_id)
        self.assertEqual(found.scopus_id, article.scopus_id)

    def test_find_by_id_returns_none_when_missing(self):
        self.assertIsNone(self.service.find_by_id(uid()))

    def test_save(self):
        scopus_id = uid()
        saved = self.service.save(
            {"scopus_id": scopus_id, "title": "New", "publication_date": "2024-01-01"}
        )
        self.assertEqual(saved.scopus_id, scopus_id)

    def test_articles_count(self):
        make_article()
        self.assertGreaterEqual(self.service.articles_count(), 1)

    def test_find_all(self):
        make_article()
        results = self.service.find_all(page_number=1, page_size=5)
        self.assertIsInstance(results, list)

    def test_bulk_create(self):
        articles = self.service.bulk_create(
            [{"scopus_id": uid(), "title": "Bulk1"}, {"scopus_id": uid(), "title": "Bulk2"}]
        )
        self.assertEqual(len(articles), 2)

    def test_find_articles_by_ids(self):
        article = make_article()
        results, total = self.service.find_articles_by_ids([article.scopus_id])
        self.assertEqual(total, 1)
        self.assertEqual(results[0]["scopus_id"], article.scopus_id)

    def test_find_articles_by_ids_without_order_by_date(self):
        article = make_article()
        results, total = self.service.find_articles_by_ids(
            [article.scopus_id], order_by_date=False
        )
        self.assertEqual(total, 1)

    def test_find_articles_by_filter_years_include(self):
        article = make_article(publication_date="2020-05-01")
        results = self.service.find_articles_by_filter_years(
            "include", ["2020"], [article.scopus_id]
        )
        self.assertEqual(len(results), 1)

    def test_find_articles_by_filter_years_exclude(self):
        article = make_article(publication_date="2020-05-01")
        results = self.service.find_articles_by_filter_years(
            "exclude", ["1999"], [article.scopus_id]
        )
        self.assertEqual(len(results), 1)

    def test_find_years_by_articles(self):
        article = make_article(publication_date="2021-01-01")
        years = self.service.find_years_by_articles([article.scopus_id])
        self.assertIn("2021-01-01", years)

    def test_find_total_articles(self):
        make_article()
        self.assertGreaterEqual(self.service.find_total_articles(), 1)

    def test_find_authors_by_article(self):
        article = make_article()
        author = make_author()
        author.articles.connect(article, {"order": 1})
        result = self.service.find_authors_by_article(article.scopus_id)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 1)

    def test_find_articles_by_author(self):
        article = make_article()
        author = make_author()
        author.articles.connect(article, {"order": 1})
        result = self.service.find_articles_by_author(author.scopus_id)
        self.assertEqual(len(result), 1)

    def test_update(self):
        article = make_article()
        updated = self.service.update({"scopus_id": article.scopus_id, "title": "Updated"})
        self.assertEqual(updated.title, "Updated")

    def test_find_most_relevant_articles_by_topic_wraps_model_errors(self):
        with patch(
            "apps.search_engine.application.services.article_service.Model",
            side_effect=RuntimeError("boom"),
        ):
            with self.assertRaises(Exception):
                self.service.find_most_relevant_articles_by_topic("ai")


class AuthorServiceTests(TestCase):
    def setUp(self):
        self.service = AuthorService()

    def test_authors_count(self):
        make_author()
        self.assertGreaterEqual(self.service.authors_count(), 1)

    def test_authors_no_updated(self):
        author = make_author()
        results = self.service.authors_no_updated()
        self.assertIn(author.scopus_id, [a.scopus_id for a in results])

    def test_get_authors_no_updated_count(self):
        make_author()
        self.assertGreaterEqual(self.service.get_authors_no_updated_count(), 1)

    def test_find_by_id(self):
        author = make_author()
        found = self.service.find_by_id(author.scopus_id)
        self.assertEqual(found.scopus_id, author.scopus_id)

    def test_find_all(self):
        make_author()
        results = self.service.find_all(page_size=5, page=1)
        self.assertIsInstance(results, list)

    def test_bulk_create(self):
        authors = self.service.bulk_create(
            [{"scopus_id": uid(), "first_name": "X"}, {"scopus_id": uid(), "first_name": "Y"}]
        )
        self.assertEqual(len(authors), 2)

    def test_save_and_update_are_noop(self):
        self.assertIsNone(self.service.save(None))
        self.assertIsNone(self.service.update(None))

    def test_find_authors_by_query_matches_name(self):
        unique_marker = uid()
        make_author(first_name=f"Zorro{unique_marker}", last_name="Perez")
        results, total = self.service.find_authors_by_query(
            f"Zorro{unique_marker}", page_size=10, page=1
        )
        self.assertEqual(total, 1)
        self.assertEqual(len(results), 1)

    def test_find_authors_by_query_no_match(self):
        results, total = self.service.find_authors_by_query(
            f"NoSuchAuthor{uid()}", page_size=10, page=1
        )
        self.assertEqual(total, 0)
        self.assertEqual(results, [])

    def test_build_diacritic_regex(self):
        regex = self.service._build_diacritic_regex("José")
        self.assertTrue(regex.startswith("(?i)"))

    def test_find_authors_by_affiliation_filter_include(self):
        author = make_author()
        affiliation = Affiliation(scopus_id=uid(), name=f"Uni {uid()}").save()
        author.affiliations.connect(affiliation)
        results = self.service.find_authors_by_affiliation_filter(
            "include", [affiliation.scopus_id], [author.scopus_id]
        )
        self.assertEqual(len(results), 1)

    def test_find_authors_by_affiliation_filter_exclude(self):
        author = make_author()
        other_affiliation = Affiliation(scopus_id=uid(), name=f"Uni {uid()}").save()
        excluded_affiliation = Affiliation(scopus_id=uid(), name=f"Uni {uid()}").save()
        author.affiliations.connect(other_affiliation)
        results = self.service.find_authors_by_affiliation_filter(
            "exclude", [excluded_affiliation.scopus_id], [author.scopus_id]
        )
        self.assertEqual(len(results), 1)

    def test_find_community(self):
        a1 = make_author()
        a2 = make_author()
        from apps.search_engine.domain.entities.coauthored import CoAuthored

        rel = a1.co_authors.connect(a2, {"collab_strength": 1.0, "shared_pubs": 1})
        rel.save()
        community = self.service.find_community([a1.scopus_id, a2.scopus_id])
        self.assertEqual(community["size_nodes"], 2)
        self.assertEqual(community["size_links"], 1)

    def test_find_most_relevant_authors_by_topic_returns_when_not_empty(self):
        mock_model = MagicMock()
        import pandas as pd

        mock_model.get_most_relevant_docs_by_topic_v2.return_value = pd.Series(
            [0.5], index=["a1"]
        )
        with patch(
            "apps.search_engine.application.services.author_service.Model",
            return_value=mock_model,
        ):
            result = self.service.find_most_relevant_authors_by_topic("ai", 5)
        self.assertFalse(result.empty)

    def test_find_most_relevant_authors_by_topic_falls_back_to_terms(self):
        import pandas as pd

        mock_model = MagicMock()

        def side_effect(term, n):
            if term == "smart grids":
                return pd.Series(dtype=float)
            return pd.Series([0.7], index=["a1"])

        mock_model.get_most_relevant_docs_by_topic_v2.side_effect = side_effect
        with patch(
            "apps.search_engine.application.services.author_service.Model",
            return_value=mock_model,
        ):
            result = self.service.find_most_relevant_authors_by_topic("smart grids", 5)
        self.assertFalse(result.empty)

    def test_find_most_relevant_authors_by_topic_wraps_errors(self):
        with patch(
            "apps.search_engine.application.services.author_service.Model",
            side_effect=RuntimeError("boom"),
        ):
            with self.assertRaises(Exception):
                self.service.find_most_relevant_authors_by_topic("ai", 5)


class AffiliationServiceTests(TestCase):
    def setUp(self):
        self.service = AffiliationService()

    def test_find_by_id(self):
        aff = Affiliation(scopus_id=uid(), name=f"Uni {uid()}").save()
        found = self.service.find_by_id(aff.scopus_id)
        self.assertEqual(found.scopus_id, aff.scopus_id)

    def test_find_total_affiliations(self):
        Affiliation(scopus_id=uid(), name=f"Uni {uid()}").save()
        self.assertGreaterEqual(self.service.find_total_affiliations(), 1)

    def test_find_all(self):
        Affiliation(scopus_id=uid(), name=f"Uni {uid()}").save()
        results = self.service.find_all(page_number=1, page_size=5)
        self.assertIsInstance(results, list)

    def test_bulk_create(self):
        results = self.service.bulk_create(
            [
                {"scopus_id": uid(), "name": f"Uni {uid()}"},
                {"scopus_id": uid(), "name": f"Uni {uid()}"},
            ]
        )
        self.assertEqual(len(results), 2)

    def test_find_by_name_save_update_are_noop(self):
        self.assertIsNone(self.service.find_by_name("x"))
        self.assertIsNone(self.service.save(None))
        self.assertIsNone(self.service.update(None))

    def test_find_affiliations_by_authors(self):
        author = make_author()
        aff = Affiliation(scopus_id=uid(), name=f"Uni {uid()}").save()
        author.affiliations.connect(aff)
        results = self.service.find_affiliations_by_authors([author.scopus_id])
        self.assertEqual(len(results), 1)

    def test_find_affiliations_by_authors_no_match(self):
        results = self.service.find_affiliations_by_authors([uid()])
        self.assertEqual(results, [])


class CoAuthoredServiceTests(TestCase):
    def test_find_coauthors_by_id_returns_nodes_and_links(self):
        author_service = AuthorService()
        service = CoAuthoredService(author_repository=author_service)
        a1 = make_author(scopus_id=nid())
        a2 = make_author(scopus_id=nid())
        rel = a1.co_authors.connect(a2, {"collab_strength": 2.0, "shared_pubs": 3})
        rel.save()
        nodes, links = service.find_coauthors_by_id(a1.scopus_id)
        self.assertEqual(len(nodes), 1)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["collabStrength"], 2.0)

    def test_find_coauthors_by_id_no_coauthors(self):
        author_service = AuthorService()
        service = CoAuthoredService(author_repository=author_service)
        a1 = make_author()
        nodes, links = service.find_coauthors_by_id(a1.scopus_id)
        self.assertEqual(nodes, [])
        self.assertEqual(links, [])

    def test_save_is_noop(self):
        service = CoAuthoredService(author_repository=AuthorService())
        self.assertIsNone(service.save(None))


class TopicServiceTests(TestCase):
    def setUp(self):
        self.service = TopicService()

    def test_find_all(self):
        Topic.from_json(f"topic-{uid()}")
        results = self.service.find_all()
        self.assertGreaterEqual(len(list(results)), 1)

    def test_topics_count(self):
        Topic.from_json(f"topic-{uid()}")
        self.assertGreaterEqual(self.service.topics_count(), 1)

    def test_find_by_id_and_related_are_noop(self):
        self.assertIsNone(self.service.find_by_id(1))
        self.assertIsNone(self.service.find_by_article_id(1))
        self.assertIsNone(self.service.find_by_author_id(1))
        self.assertIsNone(self.service.save(None))
        self.assertIsNone(self.service.update(None))
