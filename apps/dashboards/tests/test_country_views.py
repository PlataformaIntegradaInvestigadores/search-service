from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.dashboards.domain.entities.affiliation_topics import AffiliationTopics
from apps.dashboards.domain.entities.affiliation_topics_acumulated import (
    AffiliationTopicsAcumulated,
)
from apps.dashboards.domain.entities.affiliation_topics_year import AffiliationTopicsYear
from apps.dashboards.domain.entities.country_acumulated import CountryAcumulated
from apps.dashboards.domain.entities.country_topics import CountryTopics
from apps.dashboards.domain.entities.country_topics_acumulated import (
    CountryTopicsAcumulated,
)
from apps.dashboards.domain.entities.country_topics_year import CountryTopicsYear
from apps.dashboards.domain.entities.country_year import CountryYear

BASE = "/api-se/v1/dashboard/country/"

COLLECTIONS = (
    AffiliationTopics,
    AffiliationTopicsAcumulated,
    AffiliationTopicsYear,
    CountryTopics,
    CountryTopicsAcumulated,
    CountryTopicsYear,
    CountryYear,
)


class CountryViewsTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        for model in COLLECTIONS:
            model.drop_collection()

    def tearDown(self):
        for model in COLLECTIONS:
            model.drop_collection()

    def test_get_topics(self):
        CountryTopics.objects.create(topic_name="IA", total_articles=5)
        response = self.client.get(f"{BASE}get_topics/", {"number_top": 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["text"], "IA")

    def test_get_topics_acumulated(self):
        CountryTopicsAcumulated.objects.create(
            topic_name="IA", year=2020, total_articles=5
        )
        response = self.client.get(
            f"{BASE}get_topics_acumulated/", {"topic": "IA", "year": 2020}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_acumulated(self):
        CountryAcumulated = __import__(
            "apps.dashboards.domain.entities.country_acumulated",
            fromlist=["CountryAcumulated"],
        ).CountryAcumulated
        CountryAcumulated.drop_collection()
        CountryAcumulated.objects.create(
            year=2020,
            total_authors=1,
            total_articles=2,
            total_affiliations=3,
            total_topics=4,
        )
        response = self.client.get(f"{BASE}get_acumulated/", {"year": 2020})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["author"], 1)
        CountryAcumulated.drop_collection()

    def test_get_year(self):
        CountryYear.objects.create(
            year=2020,
            total_authors=1,
            total_articles=2,
            total_affiliations=3,
            total_topics=4,
        )
        response = self.client.get(f"{BASE}get_year/", {"year": 2020})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["article"], 2)

    def test_get_year_not_found_returns_500(self):
        response = self.client.get(f"{BASE}get_year/", {"year": 9999})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_get_top_topics(self):
        CountryTopicsAcumulated.objects.create(
            topic_name="IA", year=2020, total_articles=5
        )
        response = self.client.get(f"{BASE}get_top_topics/", {"year": 2020})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["text"], "IA")

    def test_get_top_topics_year(self):
        CountryTopicsYear.objects.create(topic_name="IA", year=2020, total_articles=5)
        response = self.client.get(f"{BASE}get_top_topics_year/", {"year": 2020})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["text"], "IA")

    def test_get_last_years(self):
        CountryYear.objects.create(
            year=2020,
            total_authors=1,
            total_articles=2,
            total_affiliations=3,
            total_topics=4,
        )
        response = self.client.get(f"{BASE}get_last_years/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["year"], 2020)

    def test_get_years(self):
        CountryYear.objects.create(
            year=2020,
            total_authors=1,
            total_articles=2,
            total_affiliations=3,
            total_topics=4,
        )
        response = self.client.get(f"{BASE}get_years/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["year"], 2020)

    def test_get_year_info(self):
        CountryYear.objects.create(
            year=2020,
            total_authors=1,
            total_articles=2,
            total_affiliations=3,
            total_topics=4,
        )
        response = self.client.get(f"{BASE}get_year_info/", {"year": 2020})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["article"], 2)

    def test_get_range_info(self):
        CountryYear.objects.create(
            year=2005,
            total_authors=1,
            total_articles=2,
            total_affiliations=3,
            total_topics=4,
        )
        response = self.client.get(f"{BASE}get_range_info/", {"year": 2010})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_search(self):
        CountryTopics.objects.create(topic_name="Artificial Intelligence", total_articles=5)
        response = self.client.get(f"{BASE}search/", {"query": "Artificial"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_topics_years(self):
        CountryTopicsYear.objects.create(topic_name="IA", year=2020, total_articles=5)
        response = self.client.get(f"{BASE}get_topics_years/", {"topic": "IA"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["year"], 2020)

    def test_get_topics_affiliations(self):
        AffiliationTopics.objects.create(
            scopus_id=1, name="Uni A", topic_name="IA", total_articles=5
        )
        response = self.client.get(f"{BASE}get_topics_affiliations/", {"topic": "IA"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["text"], "Uni A")

    def test_get_topics_affiliations_year(self):
        AffiliationTopicsYear.objects.create(
            scopus_id=1, name="Uni A", topic_name="IA", year=2020, total_articles=5
        )
        response = self.client.get(
            f"{BASE}get_topics_affiliations_year/", {"topic": "IA", "year": 2020}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["text"], "Uni A")

    def test_get_topics_affiliations_acumulated(self):
        AffiliationTopicsAcumulated.objects.create(
            scopus_id=1, name="Uni A", topic_name="IA", year=2020, total_articles=5
        )
        response = self.client.get(
            f"{BASE}get_topics_affiliations_acumulated/", {"topic": "IA", "year": 2020}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["text"], "Uni A")

    def test_get_topics_year_info(self):
        CountryTopicsYear.objects.create(topic_name="IA", year=2020, total_articles=5)
        response = self.client.get(f"{BASE}get_topics_year_info/", {"topic": "IA"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_topics_year(self):
        CountryTopicsYear.objects.create(topic_name="IA", year=2020, total_articles=5)
        response = self.client.get(
            f"{BASE}get_topics_year/", {"topic": "IA", "year": 2020}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_topics_range_year(self):
        CountryTopicsYear.objects.create(topic_name="IA", year=2005, total_articles=5)
        response = self.client.get(
            f"{BASE}get_topics_range_year/", {"topic": "IA", "year": 2010}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_topics_summary(self):
        CountryTopics.objects.create(topic_name="IA", total_articles=5)
        AffiliationTopics.objects.create(
            scopus_id=1, name="Uni A", topic_name="IA", total_articles=5
        )
        response = self.client.get(f"{BASE}get_topics_summary/", {"topic": "IA"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["articles"], 5)
        self.assertEqual(response.data["affiliations"], 1)

    def test_get_topics_summary_year(self):
        CountryTopicsYear.objects.create(topic_name="IA", year=2020, total_articles=5)
        AffiliationTopicsYear.objects.create(
            scopus_id=1, name="Uni A", topic_name="IA", year=2020, total_articles=5
        )
        response = self.client.get(
            f"{BASE}get_topics_summary_year/", {"topic": "IA", "year": 2020}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["affiliations"], 1)

    def test_get_topics_summary_acumulated(self):
        CountryTopicsAcumulated.objects.create(
            topic_name="IA", year=2020, total_articles=5
        )
        AffiliationTopicsAcumulated.objects.create(
            scopus_id=1, name="Uni A", topic_name="IA", year=2020, total_articles=5
        )
        response = self.client.get(
            f"{BASE}get_topics_summary_acumulated/", {"topic": "IA", "year": 2020}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["affiliations"], 1)

    def test_get_topics_acumulated_sin_datos_retorna_lista_vacia(self):
        # topic/year sin coincidencias: get_topics_acumulated_by_year solo
        # filtra, no lanza excepcion, asi que responde 200 con lista vacia
        # (no es un error real, a diferencia de los demas casos de este archivo).
        response = self.client.get(
            f"{BASE}get_topics_acumulated/", {"topic": "Missing", "year": 2099}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_error_branches_return_500(self):
        error_cases = [
            (f"{BASE}get_topics/", {"number_top": "bad"}),
            (f"{BASE}get_acumulated/", {"year": 9999}),
            (f"{BASE}get_top_topics_year/", {"year": "bad"}),
            (f"{BASE}get_range_info/", {"year": "bad"}),
            (f"{BASE}get_topics_year/", {"topic": "Missing", "year": 2099}),
            (
                f"{BASE}get_topics_summary/",
                {"topic": "Missing"},
            ),
            (
                f"{BASE}get_topics_summary_year/",
                {"topic": "Missing", "year": 2099},
            ),
            (
                f"{BASE}get_topics_summary_acumulated/",
                {"topic": "Missing", "year": 2099},
            ),
        ]
        for url, params in error_cases:
            with self.subTest(url=url):
                response = self.client.get(url, params)
                self.assertEqual(
                    response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
                )
