"""PopulateService: la logica de agregacion (get_*_dict) recibe filas crudas
de Neo4j via db.cypher_query -- se mockea esa llamada con filas sinteticas y
se deja correr el resto de la logica (incluyendo el guardado real en Mongo,
contra el contenedor de test) para cubrir tanto el mapeo como el populate_*.
"""

from unittest.mock import patch

from django.test import TestCase

from apps.dashboards.application.services.populate_service import PopulateService
from apps.dashboards.domain.entities.affiliation import Affiliation
from apps.dashboards.domain.entities.affiliation_topics import AffiliationTopics
from apps.dashboards.domain.entities.affiliation_topics_acumulated import (
    AffiliationTopicsAcumulated,
)
from apps.dashboards.domain.entities.affiliation_topics_year import AffiliationTopicsYear
from apps.dashboards.domain.entities.affiliation_year import AffiliationYear
from apps.dashboards.domain.entities.affiliation_year_acumulated import (
    AffiliationAcumulated,
)
from apps.dashboards.domain.entities.author import Author
from apps.dashboards.domain.entities.author_topics import AuthorTopics
from apps.dashboards.domain.entities.author_topics_acumulated import (
    AuthorTopicsAcumulated,
)
from apps.dashboards.domain.entities.author_topics_year import AuthorTopicsYear
from apps.dashboards.domain.entities.author_year import AuthorYear
from apps.dashboards.domain.entities.author_year_acumulated import AuthorAcumulated
from apps.dashboards.domain.entities.country_acumulated import CountryAcumulated
from apps.dashboards.domain.entities.country_topics import CountryTopics
from apps.dashboards.domain.entities.country_topics_acumulated import (
    CountryTopicsAcumulated,
)
from apps.dashboards.domain.entities.country_topics_year import CountryTopicsYear
from apps.dashboards.domain.entities.country_year import CountryYear
from apps.dashboards.domain.entities.province import Province
from apps.dashboards.domain.entities.province_acumulated import ProvinceAcumulated
from apps.dashboards.domain.entities.province_topics_acumulated import (
    ProvinceTopicsAcumulated,
)
from apps.dashboards.domain.entities.province_topics_year import ProvinceTopicsYear
from apps.dashboards.domain.entities.province_year import ProvinceYear

CYPHER_QUERY_PATH = "apps.dashboards.application.services.populate_service.db.cypher_query"


class PopulateServiceBase(TestCase):
    def setUp(self):
        self.service = PopulateService()
        for model in self.service.DASHBOARD_COLLECTIONS:
            model.drop_collection()

    def tearDown(self):
        for model in self.service.DASHBOARD_COLLECTIONS:
            model.drop_collection()


class PopulateProvinceTests(PopulateServiceBase):
    def test_populate_province_maps_neo4j_rows_into_mongo(self):
        rows = [
            (1, "Uni A", "Quito", 100, "2020-01-01", "IA"),
            (1, "Uni A", "Quito", 101, "2021-01-01", "IA"),
        ]
        with patch(CYPHER_QUERY_PATH, return_value=(rows, None)):
            self.service.populate_province()

        provinces = list(Province.objects.all())
        self.assertEqual(len(provinces), 1)
        self.assertEqual(provinces[0].total_articles, 2)
        years = {p.year: p.total_articles for p in ProvinceYear.objects.all()}
        self.assertEqual(years, {2020: 1, 2021: 1})
        acumulated = {p.year: p.total_articles for p in ProvinceAcumulated.objects.all()}
        self.assertEqual(acumulated, {2020: 1, 2021: 2})
        topics_year = list(ProvinceTopicsYear.objects.all())
        self.assertEqual(len(topics_year), 2)
        topics_acumulated = {
            t.year: t.total_articles for t in ProvinceTopicsAcumulated.objects.all()
        }
        self.assertEqual(topics_acumulated, {2020: 1, 2021: 1})

    def test_populate_province_skips_null_city(self):
        rows = [(1, "Uni A", None, 100, "2020-01-01", "IA")]
        with patch(CYPHER_QUERY_PATH, return_value=(rows, None)):
            self.service.populate_province()
        self.assertEqual(Province.objects.count(), 0)


class PopulateAuthorTests(PopulateServiceBase):
    def test_populate_author_maps_neo4j_rows_into_mongo(self):
        rows = [
            (1, 100, "2020-01-01", "IA"),
            (1, 101, "2021-01-01", "IA"),
            (2, 102, "2020-01-01", "ML"),
        ]
        with patch(CYPHER_QUERY_PATH, return_value=(rows, None)):
            self.service.populate_author()

        authors = {a.scopus_id: a.total_articles for a in Author.objects.all()}
        self.assertEqual(authors, {1: 2, 2: 1})
        author_years = {
            (a.scopus_id, a.year): a.total_articles for a in AuthorYear.objects.all()
        }
        self.assertEqual(
            author_years, {(1, 2020): 1, (1, 2021): 1, (2, 2020): 1}
        )
        acumulated = {
            (a.scopus_id, a.year): a.total_articles
            for a in AuthorAcumulated.objects.all()
        }
        self.assertEqual(acumulated, {(1, 2020): 1, (1, 2021): 2, (2, 2020): 1})
        topics = {t.scopus_id: t.total_articles for t in AuthorTopics.objects.all()}
        self.assertEqual(topics, {1: 2, 2: 1})
        self.assertEqual(AuthorTopicsYear.objects.count(), 3)
        self.assertEqual(AuthorTopicsAcumulated.objects.count(), 3)


class PopulateCountryTests(PopulateServiceBase):
    def test_populate_country_maps_neo4j_rows_into_mongo(self):
        articles_rows = [
            (100, "2020-01-01", "IA"),
            (101, "2021-01-01", "IA"),
        ]
        authors_rows = [
            (1, 100, "2020-01-01", "IA"),
            (2, 101, "2021-01-01", "IA"),
        ]
        affiliations_rows = [
            (10, "Uni A", 100, "2020-01-01", "IA"),
        ]

        def fake_cypher_query(query):
            if "au:Author" in query:
                return authors_rows, None
            if "af:Affiliation" in query:
                return affiliations_rows, None
            return articles_rows, None

        with patch(CYPHER_QUERY_PATH, side_effect=fake_cypher_query):
            self.service.populate_country()

        self.assertEqual(CountryYear.objects.count(), 2)
        self.assertEqual(CountryAcumulated.objects.count(), 2)
        self.assertGreaterEqual(CountryTopicsYear.objects.count(), 1)
        self.assertGreaterEqual(CountryTopics.objects.count(), 1)
        self.assertGreaterEqual(CountryTopicsAcumulated.objects.count(), 1)

        year_2020 = CountryYear.objects.get(year=2020)
        self.assertEqual(year_2020.total_articles, 1)
        self.assertEqual(year_2020.total_authors, 1)
        self.assertEqual(year_2020.total_affiliations, 1)


class PopulateAffiliationTests(PopulateServiceBase):
    def test_populate_affiliation_maps_neo4j_rows_into_mongo(self):
        rows = [
            (10, "Uni A", 100, "2020-01-01", "IA"),
            (10, "Uni A", 101, "2021-01-01", "ML"),
        ]
        with patch(CYPHER_QUERY_PATH, return_value=(rows, None)):
            self.service.populate_affiliation()

        affiliations = list(Affiliation.objects.all())
        self.assertEqual(len(affiliations), 1)
        self.assertEqual(affiliations[0].total_articles, 2)
        self.assertEqual(AffiliationYear.objects.count(), 2)
        self.assertEqual(AffiliationAcumulated.objects.count(), 2)
        self.assertEqual(AffiliationTopicsYear.objects.count(), 2)
        self.assertEqual(AffiliationTopicsAcumulated.objects.count(), 2)
        self.assertEqual(AffiliationTopics.objects.count(), 2)


class PopulateOrchestratorTests(PopulateServiceBase):
    def test_populate_calls_drop_then_each_populate_step_in_order(self):
        call_order = []
        with (
            patch.object(
                self.service, "drop_database", side_effect=lambda: call_order.append("drop")
            ),
            patch.object(
                self.service,
                "populate_country",
                side_effect=lambda: call_order.append("country"),
            ),
            patch.object(
                self.service,
                "populate_affiliation",
                side_effect=lambda: call_order.append("affiliation"),
            ),
            patch.object(
                self.service,
                "populate_province",
                side_effect=lambda: call_order.append("province"),
            ),
            patch.object(
                self.service,
                "populate_author",
                side_effect=lambda: call_order.append("author"),
            ),
        ):
            self.service.populate()

        self.assertEqual(
            call_order, ["drop", "country", "affiliation", "province", "author"]
        )
