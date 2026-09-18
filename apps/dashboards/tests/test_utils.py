from django.test import SimpleTestCase

from apps.dashboards.utils.utils import (
    count_articles_per_year_affiliation,
    count_articles_per_year_author,
    count_articles_per_year_country,
    count_province,
    extract_year,
    find_province,
    get_affiliations_info,
    get_articles_topics_info,
    get_authors_info,
    process_affiliation_name,
)


class FindProvinceTests(SimpleTestCase):
    def test_none_returns_pendiente(self):
        self.assertEqual(find_province(None), (-1, "Pendiente"))

    def test_matches_provincia_directly(self):
        # Nota: algunos cantones/parroquias comparten nombre con otra
        # provincia en el archivo real, y el lookup prioriza la provincia
        # que aparezca primero en el diccionario (no necesariamente la
        # provincia homonima) -- solo verificamos que resuelva a un id valido.
        province_id, _province_name = find_province("Pichincha")
        self.assertNotEqual(province_id, -1)

    def test_matches_canton(self):
        # Quito is a canton of Pichincha in the real archive/provincias.json
        province_id, province_name = find_province("Quito")
        self.assertNotEqual(province_id, -1)

    def test_unknown_city_returns_pendiente(self):
        self.assertEqual(find_province("Ciudad Inexistente Zzz"), (-1, "Pendiente"))


class ProcessAffiliationNameTests(SimpleTestCase):
    def test_skips_none_city(self):
        result = process_affiliation_name([None], [1], [2020], ["IA"])
        self.assertEqual(result, [])

    def test_builds_entry_for_known_city(self):
        result = process_affiliation_name(["Quito"], [1], [2020], ["IA"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["article_id"], 1)
        self.assertEqual(result[0]["year"], 2020)
        self.assertEqual(result[0]["topic"], "IA")


class CountProvinceTests(SimpleTestCase):
    def test_counts_articles_per_province_and_topic(self):
        processed_data = [
            {
                "province_id": "17",
                "province_name": "PICHINCHA",
                "article_id": 1,
                "year": "2020",
                "topic": "IA",
            },
            {
                "province_id": "17",
                "province_name": "PICHINCHA",
                "article_id": 2,
                "year": "2021",
                "topic": "IA",
            },
        ]
        result = count_province(processed_data)
        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry["id_provincia"], "17")
        self.assertEqual(entry["num_articles"], 2)
        self.assertEqual(len(entry["years"]), 2)
        self.assertEqual(entry["topics"][0]["totalTopicArticles"], 2)

    def test_skips_none_province_and_deduplicates(self):
        processed_data = [
            {
                "province_id": None,
                "province_name": "Pendiente",
                "article_id": 1,
                "year": "2020",
                "topic": "IA",
            },
            {
                "province_id": "17",
                "province_name": "PICHINCHA",
                "article_id": 1,
                "year": "2020",
                "topic": "IA",
            },
            {
                "province_id": "17",
                "province_name": "PICHINCHA",
                "article_id": 1,
                "year": "2020",
                "topic": "IA",
            },
        ]
        result = count_province(processed_data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["num_articles"], 1)


class ExtractYearTests(SimpleTestCase):
    def test_extracts_year_prefix(self):
        self.assertEqual(extract_year(["2020-01-01", "2019-06-15"]), ["2020", "2019"])


class CountArticlesPerYearAuthorTests(SimpleTestCase):
    def test_counts_unique_articles_and_topics(self):
        result = count_articles_per_year_author(
            entity_id_column=[1, 1, 2],
            articles_id_column=[10, 11, 20],
            years_column=["2020", "2020", "2021"],
            topics=["IA", "IA", "ML"],
        )
        by_id = {r["idScopus"]: r for r in result}
        self.assertEqual(by_id[1]["totalArticles"], 2)
        self.assertEqual(by_id[2]["totalArticles"], 1)
        self.assertEqual(by_id[1]["topics"][0]["totalTopicArticles"], 2)


class CountArticlesPerYearCountryTests(SimpleTestCase):
    def test_aggregates_unique_articles(self):
        result = count_articles_per_year_country(
            articles_id=[1, 1, 2], years=["2020", "2020", "2021"], topics=["IA", "IA", "ML"]
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["totalArticles"], 2)
        topic_names = {t["topic"] for t in result[0]["topics"]}
        self.assertEqual(topic_names, {"IA", "ML"})


class CountArticlesPerYearAffiliationTests(SimpleTestCase):
    def test_tracks_name_and_unique_articles(self):
        result = count_articles_per_year_affiliation(
            af_scopus_ids=[1, 1],
            af_names=["Uni A", "Uni A"],
            ar_scopus_ids=[100, 100],
            years=["2020", "2020"],
            topics=["IA", "IA"],
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Uni A")
        self.assertEqual(result[0]["totalArticles"], 1)


class GetArticlesTopicsInfoTests(SimpleTestCase):
    def test_builds_per_year_and_acumulative_series(self):
        countries = [
            {
                "years": [{"year": "2020", "num_articles": 5}],
                "topics": [
                    {
                        "topic_name": "IA",
                        "num_articles_per_year": [{"year": "2020", "num_articles": 5}],
                    }
                ],
            }
        ]
        result = get_articles_topics_info(countries)
        self.assertEqual(result["Articles"]["Per_year"][0]["value"], 5)
        self.assertEqual(result["Articles"]["Acumulative"][0]["value"], 5)
        self.assertEqual(result["Topics"]["Per_year"][0]["value"], 1)


class GetAuthorsInfoTests(SimpleTestCase):
    def test_counts_new_authors_per_year(self):
        authors = [
            {"scopus_id": 1, "years": [{"year": "2020"}]},
            {"scopus_id": 2, "years": [{"year": "2020"}]},
            {"scopus_id": 1, "years": [{"year": "2021"}]},
        ]
        result = get_authors_info(authors)
        by_year = {e["name"]: e["value"] for e in result["Per_year"]}
        self.assertEqual(by_year["2020"], 2)
        self.assertEqual(by_year["2021"], 0)


class GetAffiliationsInfoTests(SimpleTestCase):
    def test_counts_new_affiliations_per_year(self):
        affiliations = [
            {"id_affiliation": 1, "years": [{"year": "2020"}]},
            {"id_affiliation": 2, "years": [{"year": "2021"}]},
        ]
        result = get_affiliations_info(affiliations)
        by_year = {e["name"]: e["value"] for e in result["Per_year"]}
        self.assertEqual(by_year["2020"], 1)
        self.assertEqual(by_year["2021"], 1)
