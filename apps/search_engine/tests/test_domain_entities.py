import random
import uuid

from django.test import TestCase

from apps.search_engine.domain.entities.affiliation import Affiliation
from apps.search_engine.domain.entities.article import Article
from apps.search_engine.domain.entities.author import Author
from apps.search_engine.domain.entities.topic import Topic


def uid():
    return uuid.uuid4().hex[:12]


def nid():
    return str(random.randint(10**8, 10**9 - 1))


class AffiliationFromDictTests(TestCase):
    def test_creates_new_affiliation(self):
        aff = Affiliation.from_dict(
            {
                "afid": uid(),
                "affilname": f"Uni {uid()}",
                "affiliation-city": "Bogota",
                "affiliation-country": "Colombia",
            }
        )
        self.assertEqual(aff.city, "Bogota")

    def test_returns_existing_by_scopus_id(self):
        afid = uid()
        name = f"Uni {uid()}"
        first = Affiliation.from_dict(
            {"afid": afid, "affilname": name, "affiliation-city": "A", "affiliation-country": "B"}
        )
        again = Affiliation.from_dict(
            {"afid": afid, "affilname": name, "affiliation-city": "A", "affiliation-country": "B"}
        )
        self.assertEqual(first.scopus_id, again.scopus_id)

    def test_updates_existing_by_name_when_scopus_id_missing(self):
        name = f"Uni {uid()}"
        new_afid = uid()
        Affiliation(scopus_id=uid(), name=name, city="Old", country="Old").save()
        updated = Affiliation.from_dict(
            {
                "afid": new_afid,
                "affilname": name,
                "affiliation-city": "New",
                "affiliation-country": "New",
            }
        )
        # from_dict overwrites the matched node's scopus_id with the incoming one.
        self.assertEqual(updated.scopus_id, new_afid)
        self.assertEqual(updated.city, "New")
        self.assertEqual(len(list(Affiliation.nodes.filter(name=name))), 1)


class AffiliationRetrieveFromJsonTests(TestCase):
    def test_returns_none_for_non_dict(self):
        self.assertIsNone(Affiliation.retrieve_from_json("not-a-dict"))

    def test_returns_none_when_ip_doc_not_dict(self):
        data = {"@affiliation-id": uid(), "ip-doc": "not-a-dict"}
        self.assertIsNone(Affiliation.retrieve_from_json(data))

    def test_returns_none_when_no_name_found(self):
        data = {"@affiliation-id": uid(), "ip-doc": {"address": {"city": "X"}}}
        self.assertIsNone(Affiliation.retrieve_from_json(data))

    def test_uses_parent_preferred_name(self):
        data = {
            "@affiliation-id": uid(),
            "ip-doc": {
                "address": {"city": "Medellin", "country": "Colombia"},
                "parent-preferred-name": {"$": f"Parent Uni {uid()}"},
            },
        }
        aff = Affiliation.retrieve_from_json(data)
        self.assertIsNotNone(aff)
        self.assertEqual(aff.city, "Medellin")

    def test_falls_back_to_preferred_name(self):
        data = {
            "@affiliation-id": uid(),
            "ip-doc": {
                "address": {"city": "Cali"},
                "preferred-name": {"$": f"Preferred Uni {uid()}"},
            },
        }
        aff = Affiliation.retrieve_from_json(data)
        self.assertIsNotNone(aff)

    def test_address_not_dict_defaults_empty(self):
        data = {
            "@affiliation-id": uid(),
            "ip-doc": {
                "address": "not-a-dict",
                "preferred-name": {"$": f"Uni {uid()}"},
            },
        }
        aff = Affiliation.retrieve_from_json(data)
        self.assertIsNotNone(aff)
        self.assertIsNone(aff.city)

    def test_non_dict_name_payload_ignored(self):
        data = {
            "@affiliation-id": uid(),
            "ip-doc": {
                "address": {},
                "parent-preferred-name": "not-a-dict",
                "preferred-name": "also-not-a-dict",
            },
        }
        self.assertIsNone(Affiliation.retrieve_from_json(data))

    def test_updates_existing_by_name(self):
        name = f"Existing Uni {uid()}"
        Affiliation(scopus_id=uid(), name=name, city="Old", country="Old").save()
        data = {
            "@affiliation-id": uid(),
            "ip-doc": {
                "address": {"city": "New", "country": "New"},
                "preferred-name": {"$": name},
            },
        }
        updated = Affiliation.retrieve_from_json(data)
        self.assertEqual(updated.city, "New")


class AuthorFromDictTests(TestCase):
    def test_raises_without_scopus_id(self):
        with self.assertRaises(ValueError):
            Author.from_dict({"given-name": "Ana"})

    def test_creates_new_author(self):
        author = Author.from_dict(
            {
                "authid": uid(),
                "given-name": "Ana",
                "surname": "Perez",
                "initials": "A.",
                "authname": "Perez A.",
            }
        )
        self.assertEqual(author.first_name, "Ana")

    def test_returns_existing_author(self):
        authid = uid()
        first = Author.from_dict({"authid": authid, "given-name": "Ana", "surname": "P"})
        again = Author.from_dict({"authid": authid, "given-name": "Ignored", "surname": "P"})
        self.assertEqual(first.scopus_id, again.scopus_id)
        self.assertEqual(again.first_name, "Ana")


class AuthorValidateScopusIdTests(TestCase):
    def test_valid_id(self):
        self.assertEqual(Author.validate_scopus_id("AUTHOR_ID:12345"), 12345)

    def test_empty_id_returns_none(self):
        self.assertIsNone(Author.validate_scopus_id(""))

    def test_non_numeric_id_returns_none(self):
        self.assertIsNone(Author.validate_scopus_id("AUTHOR_ID:not-a-number"))


class AuthorUpdateFromJsonTests(TestCase):
    def test_raises_without_valid_scopus_id(self):
        with self.assertRaises(ValueError):
            Author.update_from_json({"coredata": {"dc:identifier": ""}})

    def test_silently_ignores_missing_author(self):
        result = Author.update_from_json(
            {"coredata": {"dc:identifier": "AUTHOR_ID:999999"}}
        )
        self.assertIsNone(result)

    def test_updates_existing_author_basic_fields(self):
        author_id = nid()
        author = Author(scopus_id=author_id, first_name="Old", last_name="Old").save()
        updated = Author.update_from_json(
            {
                "coredata": {
                    "dc:identifier": f"AUTHOR_ID:{author_id}",
                    "citation-count": 5,
                },
                "author-profile": {
                    "preferred-name": {
                        "given-name": "New",
                        "surname": "Name",
                        "indexed-name": "Name N.",
                        "initials": "N.",
                    },
                    "affiliation-current": {
                        "affiliation": {
                            "ip-doc": {
                                "parent-preferred-name": {"$": "Parent Org"},
                            }
                        }
                    },
                    "affiliation-history": {"affiliation": []},
                },
                "subject-areas": {"subject-area": [{"$": "machine learning"}]},
            }
        )
        self.assertEqual(updated.first_name, "New")
        self.assertEqual(updated.citation_count, 5)
        self.assertTrue(updated.updated)
        self.assertEqual(updated.current_affiliation, "Parent Org")
        topic_names = [t.name for t in updated.topics.all()]
        self.assertIn("machine learning", topic_names)

    def test_updates_with_affiliation_current_as_list_and_afdispname_fallback(self):
        author_id = nid()
        author = Author(scopus_id=author_id, first_name="Old", last_name="Old").save()
        updated = Author.update_from_json(
            {
                "coredata": {"dc:identifier": f"AUTHOR_ID:{author_id}"},
                "author-profile": {
                    "preferred-name": {},
                    "affiliation-current": {
                        "affiliation": [
                            {
                                "ip-doc": {
                                    "afdispname": "Fallback Org",
                                    "preferred-name": None,
                                }
                            }
                        ]
                    },
                    "affiliation-history": {
                        "affiliation": {
                            "@affiliation-id": uid(),
                            "ip-doc": {"preferred-name": {"$": f"Hist Org {uid()}"}},
                        }
                    },
                },
                "subject-areas": None,
            }
        )
        self.assertEqual(updated.current_affiliation, "Fallback Org")
        self.assertEqual(len(list(updated.affiliations.all())), 1)

    def test_wraps_unexpected_errors_as_value_error(self):
        author_id = nid()
        author = Author(scopus_id=author_id, first_name="Old", last_name="Old").save()
        with self.assertRaises(ValueError):
            Author.update_from_json(
                {
                    "coredata": {"dc:identifier": f"AUTHOR_ID:{author_id}"},
                    "author-profile": "not-a-dict",
                }
            )


class ArticleValidateScopusIdTests(TestCase):
    def test_valid_id(self):
        self.assertEqual(Article.validate_scopus_id("SCOPUS_ID:98765"), "98765")

    def test_empty_id_returns_none(self):
        self.assertIsNone(Article.validate_scopus_id(""))


class ArticleCalculateCollabStrengthTests(TestCase):
    def test_calculates_strength(self):
        strength = Article.calculate_collab_strength(2, 4, 9)
        self.assertAlmostEqual(strength, 2 / (4 * 9) ** 0.5)


class ArticleFromJsonTests(TestCase):
    def test_creates_article_with_authors_affiliations_topics(self):
        scopus_id = uid()
        article_data = {
            "dc:identifier": f"SCOPUS_ID:{scopus_id}",
            "dc:title": "A Great Paper",
            "prism:doi": "10.1/xyz",
            "prism:coverDate": "2024-01-01",
            "dc:description": "abstract text",
            "authkeywords": "ai | ml",
            "affiliation": [
                {
                    "afid": uid(),
                    "affilname": f"Uni {uid()}",
                    "affiliation-city": "Bogota",
                    "affiliation-country": "Colombia",
                }
            ],
            "author": [
                {"authid": uid(), "given-name": "Ana", "surname": "P"},
                {"authid": uid(), "given-name": "Luis", "surname": "G"},
            ],
        }
        article = Article.from_json(article_data, client=None)
        self.assertEqual(article.title, "A Great Paper")
        self.assertEqual(len(list(article.affiliations.all())), 1)
        self.assertEqual(len(list(article.topics.all())), 2)

    def test_returns_existing_article_without_reprocessing(self):
        scopus_id = uid()
        article_data = {
            "dc:identifier": f"SCOPUS_ID:{scopus_id}",
            "dc:title": "First title",
            "prism:coverDate": "2024-01-01",
            "authkeywords": "",
            "affiliation": [],
            "author": [],
        }
        first = Article.from_json(article_data, client=None)
        article_data["dc:title"] = "Changed title"
        again = Article.from_json(article_data, client=None)
        self.assertEqual(again.title, "First title")
        self.assertEqual(first.scopus_id, again.scopus_id)

    def test_raises_without_valid_scopus_id(self):
        with self.assertRaises(ValueError):
            Article.from_json({"dc:identifier": ""}, client=None)

    def test_builds_coauthored_relationship_on_shared_authors(self):
        scopus_id_a = uid()
        author_id_1 = uid()
        author_id_2 = uid()
        common_authors = [
            {"authid": author_id_1, "given-name": "Ana", "surname": "P"},
            {"authid": author_id_2, "given-name": "Luis", "surname": "G"},
        ]
        Article.from_json(
            {
                "dc:identifier": f"SCOPUS_ID:{scopus_id_a}",
                "dc:title": "Paper A",
                "prism:coverDate": "2024-01-01",
                "authkeywords": "",
                "affiliation": [],
                "author": common_authors,
            },
            client=None,
        )
        scopus_id_b = uid()
        Article.from_json(
            {
                "dc:identifier": f"SCOPUS_ID:{scopus_id_b}",
                "dc:title": "Paper B",
                "prism:coverDate": "2024-06-01",
                "authkeywords": "",
                "affiliation": [],
                "author": common_authors,
            },
            client=None,
        )
        author1 = Author.nodes.get(scopus_id=author_id_1)
        author2 = Author.nodes.get(scopus_id=author_id_2)
        self.assertTrue(author1.co_authors.is_connected(author2))
        rel = author1.co_authors.relationship(author2)
        self.assertEqual(rel.shared_pubs, 2)
