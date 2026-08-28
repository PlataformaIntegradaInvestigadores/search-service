from unittest.mock import patch

from django.test import TestCase

from apps.dashboards.application.services.affiliation_service import AffiliationService
from apps.dashboards.application.services.country_service import CountryService
from apps.dashboards.application.services.populate_service import PopulateService
from apps.dashboards.application.services.province_service import ProvinceService
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
from apps.dashboards.domain.entities.country_acumulated import CountryAcumulated
from apps.dashboards.domain.entities.country_topics import CountryTopics
from apps.dashboards.domain.entities.country_topics_acumulated import (
    CountryTopicsAcumulated,
)
from apps.dashboards.domain.entities.country_topics_year import CountryTopicsYear
from apps.dashboards.domain.entities.country_year import CountryYear
from apps.dashboards.domain.entities.province import Province
from apps.dashboards.domain.entities.province_acumulated import ProvinceAcumulated
from apps.dashboards.domain.entities.province_year import ProvinceYear


class CountryServiceTests(TestCase):
    def setUp(self):
        for model in (
            CountryYear,
            CountryAcumulated,
            CountryTopics,
            CountryTopicsYear,
            CountryTopicsAcumulated,
        ):
            model.drop_collection()
        self.service = CountryService()

    def tearDown(self):
        for model in (
            CountryYear,
            CountryAcumulated,
            CountryTopics,
            CountryTopicsYear,
            CountryTopicsAcumulated,
        ):
            model.drop_collection()

    def test_get_year_info_and_get_year(self):
        CountryYear.objects.create(
            year=2020,
            total_authors=1,
            total_articles=2,
            total_affiliations=3,
            total_topics=4,
        )
        self.assertEqual(self.service.get_year_info(2020).total_articles, 2)
        self.assertEqual(self.service.get_year(2020).total_articles, 2)

    def test_get_range_info_excludes_pre_2000(self):
        CountryYear.objects.create(year=1999, total_authors=0, total_articles=0)
        CountryYear.objects.create(year=2005, total_authors=0, total_articles=1)
        CountryYear.objects.create(year=2010, total_authors=0, total_articles=2)
        years = [y.year for y in self.service.get_range_info(2010)]
        self.assertEqual(years, [2005, 2010])

    def test_get_acumulated_by_year(self):
        CountryAcumulated.objects.create(year=2021, total_authors=1, total_articles=5)
        self.assertEqual(self.service.get_acumulated_by_year(2021).total_articles, 5)

    def test_get_topics_by_year(self):
        CountryTopicsYear.objects.create(topic_name="IA", year=2020, total_articles=7)
        result = self.service.get_topics_by_year("IA", 2020)
        self.assertEqual(result.total_articles, 7)

    def test_get_topics_acumulated_by_year_uses_topic_name_field(self):
        # Regresion: el metodo original filtraba por el campo inexistente
        # "topic" en vez de "topic_name" y CountryTopicsAcumulated no es un
        # DynamicDocument, asi que mongoengine rechazaba la query
        # (InvalidQueryError) en cada llamada real desde
        # CountryTopicsAcumulatedUseCase / get_topics_acumulated view.
        CountryTopicsAcumulated.objects.create(
            topic_name="IA", year=2020, total_articles=9
        )
        result = list(self.service.get_topics_acumulated_by_year("IA", 2020))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].total_articles, 9)

    def test_get_topics_filters_blank_and_orders_by_total(self):
        CountryTopics.objects.create(topic_name="", total_articles=100)
        CountryTopics.objects.create(topic_name=" ", total_articles=100)
        CountryTopics.objects.create(topic_name="IA", total_articles=10)
        CountryTopics.objects.create(topic_name="ML", total_articles=20)
        result = [t.topic_name for t in self.service.get_topics(2)]
        self.assertEqual(result, ["ML", "IA"])

    def test_get_top_topics(self):
        CountryTopicsAcumulated.objects.create(
            topic_name="IA", year=2020, total_articles=10
        )
        CountryTopicsAcumulated.objects.create(
            topic_name="", year=2020, total_articles=999
        )
        result = list(self.service.get_top_topics(2020))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].topic_name, "IA")

    def test_get_last_years_excludes_1999_and_earlier(self):
        CountryYear.objects.create(year=1999, total_authors=0, total_articles=0)
        years = [y.year for y in self.service.get_last_years()]
        self.assertEqual(years, [])
        CountryYear.objects.create(year=2000, total_authors=0, total_articles=0)
        years = [y.year for y in self.service.get_last_years()]
        self.assertEqual(years, [2000])

    def test_get_top_topics_by_year(self):
        CountryTopicsYear.objects.create(topic_name="IA", year=2020, total_articles=5)
        CountryTopicsYear.objects.create(topic_name=" ", year=2020, total_articles=999)
        result = list(self.service.get_top_topics_by_year(2020))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].topic_name, "IA")


class AffiliationServiceTests(TestCase):
    def setUp(self):
        for model in (
            Affiliation,
            AffiliationYear,
            AffiliationAcumulated,
            AffiliationTopicsYear,
            AffiliationTopicsAcumulated,
        ):
            model.drop_collection()
        self.service = AffiliationService()

    def tearDown(self):
        for model in (
            Affiliation,
            AffiliationYear,
            AffiliationAcumulated,
            AffiliationTopicsYear,
            AffiliationTopicsAcumulated,
        ):
            model.drop_collection()

    def test_get_affiliation_and_top_affiliations(self):
        Affiliation.objects.create(scopus_id=1, name="Uni A", total_articles=10)
        Affiliation.objects.create(scopus_id=2, name="Uni B", total_articles=20)
        self.assertEqual(self.service.get_affiliation(1).name, "Uni A")
        top = [a.scopus_id for a in self.service.get_top_affiliations()]
        self.assertEqual(top, [2, 1])

    def test_get_affiliations_by_year(self):
        AffiliationYear.objects.create(
            scopus_id=1, name="Uni A", year=2020, total_articles=5, total_topics=1
        )
        result = list(self.service.get_affiliations_by_year(2020))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].scopus_id, 1)

    def test_get_affiliation_year_and_acumulated(self):
        AffiliationYear.objects.create(
            scopus_id=1, name="Uni A", year=2020, total_articles=5, total_topics=1
        )
        AffiliationAcumulated.objects.create(
            scopus_id=1, name="Uni A", year=2020, total_articles=5, total_topics=1
        )
        self.assertEqual(
            self.service.get_affiliation_year(1, 2020).total_articles, 5
        )
        self.assertEqual(
            self.service.get_affiliation_year_acumulated(1, 2020).total_articles, 5
        )

    def test_get_affiliation_topic_and_topics_acumulated(self):
        AffiliationTopicsYear.objects.create(
            scopus_id=1, name="Uni A", topic_name="IA", year=2020, total_articles=3
        )
        AffiliationTopicsAcumulated.objects.create(
            scopus_id=1, name="Uni A", topic_name="IA", year=2020, total_articles=3
        )
        self.assertEqual(self.service.get_affiliation_topic(1, 2020).total_articles, 3)
        self.assertEqual(
            self.service.get_affiliation_topics_acumulated(1, 2020).total_articles, 3
        )

    def test_get_top_affiliations_acumulated(self):
        AffiliationAcumulated.objects.create(
            scopus_id=1, name="Uni A", year=2020, total_articles=5, total_topics=1
        )
        AffiliationAcumulated.objects.create(
            scopus_id=2, name="Uni B", year=2020, total_articles=15, total_topics=1
        )
        result = [a.scopus_id for a in self.service.get_top_affiliations_acumulated(2020)]
        self.assertEqual(result, [2, 1])

    def test_get_last_years_excludes_pre_2000(self):
        AffiliationAcumulated.objects.create(
            scopus_id=1, name="Uni A", year=1999, total_articles=1, total_topics=0
        )
        AffiliationAcumulated.objects.create(
            scopus_id=1, name="Uni A", year=2001, total_articles=2, total_topics=0
        )
        result = [a.year for a in self.service.get_last_years(1)]
        self.assertEqual(result, [2001])


class ProvinceServiceTests(TestCase):
    def setUp(self):
        for model in (Province, ProvinceYear, ProvinceAcumulated):
            model.drop_collection()
        self.service = ProvinceService()

    def tearDown(self):
        for model in (Province, ProvinceYear, ProvinceAcumulated):
            model.drop_collection()

    def test_get_provinces_info_excludes_pendiente(self):
        Province.objects.create(province_name="Pichincha", total_articles=10)
        Province.objects.create(province_name="Pendiente", total_articles=5)
        names = [p.province_name for p in self.service.get_provinces_info()]
        self.assertEqual(names, ["Pichincha"])

    def test_get_provinces_year_excludes_pendiente(self):
        ProvinceYear.objects.create(
            province_name="Pichincha", year=2020, total_articles=10
        )
        ProvinceYear.objects.create(
            province_name="Pendiente", year=2020, total_articles=5
        )
        names = [p.province_name for p in self.service.get_provinces_year(2020)]
        self.assertEqual(names, ["Pichincha"])

    def test_get_provinces_acumulated_excludes_pendiente(self):
        ProvinceAcumulated.objects.create(
            province_name="Pichincha", year=2020, total_articles=10
        )
        ProvinceAcumulated.objects.create(
            province_name="Pendiente", year=2020, total_articles=5
        )
        names = [p.province_name for p in self.service.get_provinces_acumulated(2020)]
        self.assertEqual(names, ["Pichincha"])

    def test_unimplemented_methods_return_none(self):
        # Estos 4 metodos del interface ProvinceRepository nunca se
        # implementaron (siguen como "pass") y no tienen ningun caller real
        # en use_cases/views (confirmado via grep) -- documentamos el estado
        # actual en vez de inventar un comportamiento no especificado.
        self.assertIsNone(self.service.get_province_year("Pichincha", 2020))
        self.assertIsNone(self.service.get_province_acumulated("Pichincha", 2020))
        self.assertIsNone(self.service.get_province_topic_year(2020))
        self.assertIsNone(self.service.get_province_topic_acumulated(2020))


class PopulateServiceDropDatabaseTests(TestCase):
    def test_drop_database_survives_individual_collection_errors(self):
        service = PopulateService()
        with patch.object(
            Affiliation, "drop_collection", side_effect=Exception("boom")
        ):
            # No debe propagar la excepcion: cada coleccion se dropea de
            # forma independiente y un fallo en una no debe abortar el resto.
            service.drop_database()

    def test_get_affiliations_authors_dict_builds_query_but_never_runs_it(self):
        # Bug real mas no alcanzable: arma la consulta cypher pero nunca
        # llama a db.cypher_query(query) ni retorna nada -- cae al final del
        # metodo y retorna None implicitamente. No tiene ningun caller en
        # use_cases/views (confirmado via grep), asi que no afecta ningun
        # endpoint real; se deja documentado en vez de adivinar el shape de
        # retorno que se pretendia.
        service = PopulateService()
        self.assertIsNone(service.get_affiliations_authors_dict())

    def test_get_affiliations_topics_dict_and_articles_dict_are_unimplemented(self):
        service = PopulateService()
        self.assertIsNone(service.get_affiliations_topics_dict())
        self.assertIsNone(service.get_affiliations_articles_dict())
