"""Las consultas Cypher reciben los valores del cliente como parametros.

Antes se armaban con f-strings (IDs de afiliacion, anios, nombre de busqueda), de
modo que una comilla en el valor alteraba la consulta. Estas pruebas simulan
``db.cypher_query`` y comprueban que el texto de la consulta no contiene el valor
y que este viaja en los parametros.
"""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.search_engine.application.services.affiliation_service import (
    AffiliationService,
)
from apps.search_engine.application.services.article_service import ArticleService
from apps.search_engine.application.services.author_service import AuthorService
from apps.search_engine.application.services.coauthored_service import (
    CoAuthoredService,
)

PAYLOAD = "x'\"]) MATCH (n) DETACH DELETE n //"
SERVICES = "apps.search_engine.application.services"


def _queries(mock_query):
    """(texto, parametros) de cada llamada a ``db.cypher_query``."""
    calls = []
    for call in mock_query.call_args_list:
        text = call.args[0]
        params = call.args[1] if len(call.args) > 1 else call.kwargs.get("params")
        calls.append((text, params))
    return calls


class AuthorCypherParametersTests(SimpleTestCase):
    def setUp(self):
        self.service = AuthorService()

    def test_affiliation_filter_sends_ids_as_parameters(self):
        for filter_type in ("include", "exclude"):
            with patch(
                f"{SERVICES}.author_service.db.cypher_query", return_value=([], None)
            ) as query:
                self.service.find_authors_by_affiliation_filter(
                    filter_type, [PAYLOAD], ["1", 2]
                )

            text, params = _queries(query)[0]
            self.assertNotIn(PAYLOAD, text)
            self.assertNotIn("DETACH", text)
            self.assertEqual(params["affiliations_ids"], [PAYLOAD])
            self.assertEqual(params["authors_ids"], ["1", "2"])
            self.assertEqual("NOT aff" in text, filter_type == "exclude")

    def test_name_search_sends_the_pattern_as_a_parameter(self):
        with patch(
            f"{SERVICES}.author_service.db.cypher_query",
            side_effect=[([[0]], None), ([], None)],
        ) as query:
            authors, total = self.service.find_authors_by_query(
                "x' OR 1=1 //", page_size=10, page=3
            )

        self.assertEqual((authors, total), ([], 0))
        count, fetch = _queries(query)
        for text, params in (count, fetch):
            self.assertNotIn("1=1", text)
            self.assertNotIn("'x'", text)
            # La comilla llega intacta al parametro: ya no puede cerrar un literal.
            self.assertIn("x' ", params["pattern"])
            self.assertIn("1=1", params["pattern"])
        self.assertEqual(fetch[1]["skip"], 20)
        self.assertEqual(fetch[1]["limit"], 10)
        self.assertIn("SKIP $skip LIMIT $limit", fetch[0])

    def test_pagination_must_be_numeric(self):
        with patch(f"{SERVICES}.author_service.db.cypher_query") as query:
            with self.assertRaises(Exception):
                self.service.find_all(page_size="5; MATCH (n) DELETE n", page=2)
        query.assert_not_called()

    def test_community_sends_ids_as_parameters(self):
        with (
            patch(f"{SERVICES}.author_service.Author") as author,
            patch(
                f"{SERVICES}.author_service.db.cypher_query",
                return_value=([[[]]], None),
            ) as query,
        ):
            author.nodes.filter.return_value = []
            self.service.find_community([PAYLOAD, "7"])

        text, params = _queries(query)[0]
        self.assertNotIn(PAYLOAD, text)
        self.assertEqual(params["auth_list"], [PAYLOAD, "7"])


class ArticleCypherParametersTests(SimpleTestCase):
    def setUp(self):
        self.service = ArticleService()

    def test_year_filter_sends_years_as_parameters(self):
        for filter_type in ("include", "exclude"):
            with patch(
                f"{SERVICES}.article_service.db.cypher_query", return_value=([], None)
            ) as query:
                self.service.find_articles_by_filter_years(
                    filter_type, [PAYLOAD, 2020], ["a1"]
                )

            text, params = _queries(query)[0]
            self.assertNotIn(PAYLOAD, text)
            self.assertNotIn("DETACH", text)
            self.assertEqual(params["years"], [PAYLOAD, "2020"])
            self.assertEqual(params["ids"], ["a1"])
            self.assertEqual("NOT any" in text, filter_type == "exclude")

    def test_empty_year_filter_builds_a_valid_query(self):
        with patch(
            f"{SERVICES}.article_service.db.cypher_query", return_value=([], None)
        ) as query:
            self.assertEqual(
                self.service.find_articles_by_filter_years("include", [], ["a1"]), []
            )

        self.assertEqual(_queries(query)[0][1]["years"], [])

    def test_find_by_ids_sends_ids_and_pagination_as_parameters(self):
        row = [MagicMock(), 0, 0, [], []]
        with (
            patch(
                f"{SERVICES}.article_service.db.cypher_query",
                side_effect=[([[1]], None), ([], None)],
            ) as query,
            patch(f"{SERVICES}.article_service.Article.inflate", return_value=row[0]),
        ):
            self.service.find_articles_by_ids([PAYLOAD], page=2, page_size=5)

        count, fetch = _queries(query)
        self.assertNotIn(PAYLOAD, count[0])
        self.assertNotIn(PAYLOAD, fetch[0])
        self.assertEqual(count[1], {"ids": [PAYLOAD]})
        self.assertEqual(fetch[1], {"ids": [PAYLOAD], "skip": 5, "limit": 5})

    def test_years_by_articles_sends_ids_as_parameters(self):
        with patch(
            f"{SERVICES}.article_service.db.cypher_query", return_value=([], None)
        ) as query:
            self.service.find_years_by_articles([PAYLOAD])

        text, params = _queries(query)[0]
        self.assertNotIn(PAYLOAD, text)
        self.assertEqual(params, {"ids": [PAYLOAD]})

    def test_find_all_sends_pagination_as_parameters(self):
        with patch(
            f"{SERVICES}.article_service.db.cypher_query", return_value=([], None)
        ) as query:
            self.service.find_all(page_number=3, page_size=10)

        text, params = _queries(query)[0]
        self.assertEqual(params, {"skip": 20, "limit": 10})
        self.assertIn("SKIP $skip LIMIT $limit", text)


class AffiliationAndCoauthorCypherParametersTests(SimpleTestCase):
    def test_affiliations_find_all_sends_pagination_as_parameters(self):
        with patch(
            f"{SERVICES}.affiliation_service.db.cypher_query",
            return_value=([], None),
        ) as query:
            AffiliationService().find_all(page_number=2, page_size=4)

        self.assertEqual(_queries(query)[0][1], {"skip": 4, "limit": 4})

    def test_coauthors_network_sends_ids_as_parameters(self):
        author = MagicMock(scopus_id=PAYLOAD)
        author.co_authors.all.return_value = []
        repository = MagicMock()
        repository.find_by_id.return_value = author
        with patch(
            f"{SERVICES}.coauthored_service.db.cypher_query",
            return_value=([[None]], None),
        ) as query:
            CoAuthoredService(repository).find_coauthors_by_id("1")

        text, params = _queries(query)[0]
        self.assertNotIn(PAYLOAD, text)
        self.assertEqual(params, {"auth_list": [PAYLOAD]})
