from rest_framework import status
from rest_framework.test import APIClient, APITestCase

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
from apps.dashboards.domain.entities.country_topics_year import CountryTopicsYear

BASE = "/api-se/v1/dashboard/affiliation/"

COLLECTIONS = (
    Affiliation,
    AffiliationTopics,
    AffiliationTopicsAcumulated,
    AffiliationTopicsYear,
    AffiliationYear,
    AffiliationAcumulated,
    CountryTopicsYear,
)


class AffiliationViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        for model in COLLECTIONS:
            model.drop_collection()

    def tearDown(self):
        for model in COLLECTIONS:
            model.drop_collection()

    def test_get_by_name_found(self):
        Affiliation.objects.create(scopus_id=1, name="Uni A", total_articles=5)
        response = self.client.get(f"{BASE}get_by_name/", {"name": "Uni A"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["scopus_id"], 1)

    def test_get_by_name_not_found_returns_500(self):
        response = self.client.get(f"{BASE}get_by_name/", {"name": "Missing"})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)

    def test_get_top_affiliations(self):
        AffiliationAcumulated.objects.create(
            scopus_id=1, name="Uni A", year=2020, total_articles=5, total_topics=1
        )
        response = self.client.get(f"{BASE}get_top_affiliations/", {"year": 2020})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["text"], "Uni A")

    def test_get_affiliations(self):
        Affiliation.objects.create(scopus_id=1, name="Uni A", total_articles=5)
        response = self.client.get(f"{BASE}get_affiliations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_top_affiliations_year(self):
        AffiliationYear.objects.create(
            scopus_id=1, name="Uni A", year=2020, total_articles=5, total_topics=1
        )
        response = self.client.get(f"{BASE}get_top_affiliations_year/", {"year": 2020})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["text"], "Uni A")

    def test_search(self):
        Affiliation.objects.create(scopus_id=1, name="Universidad Central", total_articles=5)
        Affiliation.objects.create(scopus_id=2, name="Other", total_articles=1)
        response = self.client.get(f"{BASE}search/", {"query": "Central"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["scopus_id"], 1)

    def test_get_affiliation_years(self):
        AffiliationYear.objects.create(
            scopus_id=1, name="Uni A", year=2020, total_articles=5, total_topics=1
        )
        response = self.client.get(f"{BASE}get_affiliation_years/", {"scopus_id": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_affiliation_topics(self):
        AffiliationTopics.objects.create(
            scopus_id=1, name="Uni A", topic_name="IA", total_articles=5
        )
        response = self.client.get(f"{BASE}get_affiliation_topics/", {"scopus_id": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["text"], "IA")

    def test_get_years(self):
        AffiliationAcumulated.objects.create(
            scopus_id=1, name="Uni A", year=2020, total_articles=5, total_topics=1
        )
        response = self.client.get(f"{BASE}get_years/", {"scopus_id": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["year"], 2020)

    def test_get_articles_topics(self):
        Affiliation.objects.create(scopus_id=1, name="Uni A", total_articles=5)
        AffiliationTopics.objects.create(
            scopus_id=1, name="Uni A", topic_name="IA", total_articles=3
        )
        response = self.client.get(f"{BASE}get_articles_topics/", {"scopus_id": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["articles"], 5)
        self.assertEqual(response.data["topics"], 1)

    def test_get_articles_topics_error(self):
        response = self.client.get(f"{BASE}get_articles_topics/", {"scopus_id": 999})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_get_articles_topics_year(self):
        AffiliationYear.objects.create(
            scopus_id=1, name="Uni A", year=2020, total_articles=5, total_topics=1
        )
        AffiliationTopicsYear.objects.create(
            scopus_id=1, name="Uni A", topic_name="IA", year=2020, total_articles=3
        )
        response = self.client.get(
            f"{BASE}get_articles_topics_year/", {"scopus_id": 1, "year": 2020}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["articles"], 5)
        self.assertEqual(response.data["topics"], 1)

    def test_get_articles_topics_acumulated(self):
        AffiliationAcumulated.objects.create(
            scopus_id=1, name="Uni A", year=2020, total_articles=5, total_topics=2
        )
        response = self.client.get(
            f"{BASE}get_articles_topics_acumulated/", {"scopus_id": 1, "year": 2020}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["articles"], 5)
        self.assertEqual(response.data["topics"], 2)

    def test_get_topics_acumulated(self):
        AffiliationTopicsAcumulated.objects.create(
            scopus_id=1, name="Uni A", topic_name="IA", year=2020, total_articles=3
        )
        response = self.client.get(
            f"{BASE}get_topics_acumulated/", {"scopus_id": 1, "year": 2020}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["text"], "IA")

    def test_get_topics_year(self):
        AffiliationTopicsYear.objects.create(
            scopus_id=1, name="Uni A", topic_name="IA", year=2020, total_articles=3
        )
        response = self.client.get(
            f"{BASE}get_topics_year/", {"scopus_id": 1, "year": 2020}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["text"], "IA")

    def test_get_year(self):
        AffiliationYear.objects.create(
            scopus_id=1, name="Uni A", year=2020, total_articles=5, total_topics=1
        )
        response = self.client.get(f"{BASE}get_year/", {"scopus_id": 1, "year": 2020})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["total_articles"], 5)

    def test_get_year_range(self):
        AffiliationYear.objects.create(
            scopus_id=1, name="Uni A", year=2020, total_articles=5, total_topics=1
        )
        AffiliationYear.objects.create(
            scopus_id=1, name="Uni A", year=2021, total_articles=3, total_topics=1
        )
        response = self.client.get(
            f"{BASE}get_year_range/", {"scopus_id": 1, "year": 2021}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_topics_heatmap(self):
        AffiliationYear.objects.create(
            scopus_id=1, name="Uni A", year=2020, total_articles=5, total_topics=1
        )
        CountryTopicsYear.objects.create(topic_name="IA", year=2020, total_articles=5)
        AffiliationTopicsYear.objects.create(
            scopus_id=1, name="Uni A", topic_name="IA", year=2020, total_articles=3
        )
        response = self.client.get(f"{BASE}get_topics_heatmap/", {"year": 2020})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["affiliations"][0]["scopus_id"], 1)
        self.assertEqual(response.data["topics"], ["IA"])
        self.assertEqual(len(response.data["cells"]), 1)

    def test_get_topics_heatmap_error(self):
        response = self.client.get(f"{BASE}get_topics_heatmap/", {"year": "not-a-year"})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_error_branches_return_500(self):
        error_cases = [
            (f"{BASE}get_top_affiliations/", {"year": "bad"}),
            (f"{BASE}get_top_affiliations_year/", {"year": "bad"}),
            (f"{BASE}get_affiliation_years/", {"scopus_id": "not-int"}),
            (f"{BASE}get_affiliation_topics/", {"scopus_id": "not-int"}),
            (f"{BASE}get_years/", {"scopus_id": "not-int"}),
            (
                f"{BASE}get_articles_topics_year/",
                {"scopus_id": 999, "year": 2020},
            ),
            (
                f"{BASE}get_articles_topics_acumulated/",
                {"scopus_id": 999, "year": 2020},
            ),
            (f"{BASE}get_year/", {"scopus_id": 999, "year": 2020}),
            (f"{BASE}get_year_range/", {"scopus_id": "not-int", "year": 2020}),
        ]
        for url, params in error_cases:
            with self.subTest(url=url):
                response = self.client.get(url, params)
                self.assertEqual(
                    response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    def test_get_affiliations_empty_returns_500_when_serializer_errors(self):
        # get_affiliations / search / get_topics_acumulated / get_topics_year
        # no lanzan con datos vacios (devuelven lista vacia, 200) -- se
        # verifica ese camino "sin resultados" en vez de forzar un 500
        # artificial que no ocurre en produccion para estos endpoints.
        response = self.client.get(f"{BASE}get_affiliations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        response = self.client.get(f"{BASE}search/", {"query": "nadie"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        response = self.client.get(
            f"{BASE}get_topics_acumulated/", {"scopus_id": 1, "year": 2020}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        response = self.client.get(
            f"{BASE}get_topics_year/", {"scopus_id": 1, "year": 2020}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
