"""Los use_cases son wrappers delgados: solo delegan a su servicio con los
argumentos correctos. Se verifica con un mock que el servicio recibe
exactamente lo que se le paso al execute()."""

from unittest.mock import MagicMock

from django.test import SimpleTestCase

from apps.dashboards.application.use_cases.affiliation_last_years_use_case import (
    AffiliationLastYearsUseCase,
)
from apps.dashboards.application.use_cases.country_acumulated_use_case import (
    CountryAcumulatedUseCase,
)
from apps.dashboards.application.use_cases.country_topics_acumulated_use_case import (
    CountryTopicsAcumulatedUseCase,
)
from apps.dashboards.application.use_cases.country_topics_use_case import (
    CountryTopicsUseCase,
)
from apps.dashboards.application.use_cases.country_topics_year_use_case import (
    CountryTopicsYearUseCase,
)
from apps.dashboards.application.use_cases.country_year_use_case import (
    CountryYearUseCase,
)
from apps.dashboards.application.use_cases.get_affiliations_acumulated_use_case import (
    AffiliationsAcumulatedUseCase,
)
from apps.dashboards.application.use_cases.get_affiliations_use_case import (
    AffiliationsUseCase,
)
from apps.dashboards.application.use_cases.get_affiliations_year_acumulated import (
    AffiliationsYearUseCase,
)
from apps.dashboards.application.use_cases.get_provinces import ProvincesUseCase
from apps.dashboards.application.use_cases.get_provinces_acumulated_year import (
    ProvincesAcumulatedUseCase,
)
from apps.dashboards.application.use_cases.get_provinces_year_use_case import (
    ProvincesYearUseCase,
)
from apps.dashboards.application.use_cases.get_range_use_case import RangeUseCase
from apps.dashboards.application.use_cases.last_years_use_case import LastYearsUseCase
from apps.dashboards.application.use_cases.populate_use_case import PopulateUseCase
from apps.dashboards.application.use_cases.top_topics_by_year import (
    TopTopicsByYearUseCase,
)
from apps.dashboards.application.use_cases.top_topics_use_case import TopTopicsUseCase
from apps.dashboards.application.use_cases.year_info_use_case import YearInfoUseCase


class UseCaseDelegationTests(SimpleTestCase):
    def test_affiliation_last_years(self):
        service = MagicMock()
        AffiliationLastYearsUseCase(service).execute(scopus_id=1)
        service.get_last_years.assert_called_once_with(scopus_id=1)

    def test_country_acumulated(self):
        service = MagicMock()
        CountryAcumulatedUseCase(service).execute(year=2020)
        service.get_acumulated_by_year.assert_called_once_with(year=2020)

    def test_country_topics_acumulated(self):
        service = MagicMock()
        CountryTopicsAcumulatedUseCase(service).execute(topic="IA", year=2020)
        service.get_topics_acumulated_by_year.assert_called_once_with(
            topic="IA", year=2020
        )

    def test_country_topics(self):
        service = MagicMock()
        CountryTopicsUseCase(service).execute(number_top=5)
        service.get_topics.assert_called_once_with(number_top=5)

    def test_country_topics_year(self):
        service = MagicMock()
        CountryTopicsYearUseCase(service).execute(topic="IA", year=2020)
        service.get_topics_by_year.assert_called_once_with(topic="IA", year=2020)

    def test_country_year(self):
        service = MagicMock()
        CountryYearUseCase(service).execute(year=2020)
        service.get_year.assert_called_once_with(year=2020)

    def test_affiliations_acumulated(self):
        service = MagicMock()
        AffiliationsAcumulatedUseCase(service).execute(year=2020)
        service.get_top_affiliations_acumulated.assert_called_once_with(year=2020)

    def test_affiliations(self):
        service = MagicMock()
        AffiliationsUseCase(service).execute()
        service.get_top_affiliations.assert_called_once_with()

    def test_affiliations_year(self):
        service = MagicMock()
        AffiliationsYearUseCase(service).execute(year=2020)
        service.get_affiliations_by_year.assert_called_once_with(year=2020)

    def test_provinces(self):
        service = MagicMock()
        ProvincesUseCase(service).execute()
        service.get_provinces_info.assert_called_once_with()

    def test_provinces_acumulated(self):
        service = MagicMock()
        ProvincesAcumulatedUseCase(service).execute(year=2020)
        service.get_provinces_acumulated.assert_called_once_with(year=2020)

    def test_provinces_year(self):
        service = MagicMock()
        ProvincesYearUseCase(service).execute(year=2020)
        service.get_provinces_year.assert_called_once_with(year=2020)

    def test_range(self):
        service = MagicMock()
        RangeUseCase(service).execute(year=2020)
        service.get_range_info.assert_called_once_with(year=2020)

    def test_last_years(self):
        service = MagicMock()
        LastYearsUseCase(service).execute()
        service.get_last_years.assert_called_once_with()

    def test_populate(self):
        service = MagicMock()
        PopulateUseCase(service).execute()
        service.populate.assert_called_once_with()

    def test_top_topics_by_year(self):
        service = MagicMock()
        TopTopicsByYearUseCase(service).execute(year=2020)
        service.get_top_topics_by_year.assert_called_once_with(year=2020)

    def test_top_topics(self):
        service = MagicMock()
        TopTopicsUseCase(service).execute(year=2020)
        service.get_top_topics.assert_called_once_with(year=2020)

    def test_year_info(self):
        service = MagicMock()
        YearInfoUseCase(service).execute(year=2020)
        service.get_year_info.assert_called_once_with(year=2020)
