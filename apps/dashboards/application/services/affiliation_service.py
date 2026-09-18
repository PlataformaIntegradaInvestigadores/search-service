from apps.dashboards.domain.entities.affiliation import Affiliation
from apps.dashboards.domain.entities.affiliation_topics_acumulated import (
    AffiliationTopicsAcumulated,
)
from apps.dashboards.domain.entities.affiliation_topics_year import (
    AffiliationTopicsYear,
)
from apps.dashboards.domain.entities.affiliation_year import AffiliationYear
from apps.dashboards.domain.entities.affiliation_year_acumulated import (
    AffiliationAcumulated,
)
from apps.dashboards.domain.repositories.affiliation_repository import (
    AffiliationRepository,
)


class AffiliationService(AffiliationRepository):
    def get_affiliations_by_year(self, year):
        return AffiliationYear.objects(year=year).order_by("-total_articles")[:50]

    def get_affiliation_year(self, scopus_id, year):
        return AffiliationYear.objects.get(scopus_id=scopus_id, year=year)

    def get_affiliation_year_acumulated(self, scopus_id, year):
        return AffiliationAcumulated.objects.get(scopus_id=scopus_id, year=year)

    def get_affiliation_topic(self, scopus_id, year):
        return AffiliationTopicsYear.objects.get(scopus_id=scopus_id, year=year)

    def get_affiliation_topics_acumulated(self, scopus_id, year):
        return AffiliationTopicsAcumulated.objects.get(scopus_id=scopus_id, year=year)

    def get_affiliation(self, scopus_id):
        return Affiliation.objects.get(scopus_id=scopus_id)

    def get_top_affiliations_acumulated(self, year):
        return AffiliationAcumulated.objects(year=year).order_by("-total_articles")[:50]

    def get_top_affiliations(self):
        return Affiliation.objects.order_by("-total_articles")[:50]

    def get_last_years(self, scopus_id):
        return (
            AffiliationAcumulated.objects(scopus_id=scopus_id)
            .filter(year__gt=1999)
            .order_by("year")
        )
