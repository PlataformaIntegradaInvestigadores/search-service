from apps.dashboards.domain.entities.country_acumulated import CountryAcumulated
from apps.dashboards.domain.entities.country_topics import CountryTopics
from apps.dashboards.domain.entities.country_topics_acumulated import (
    CountryTopicsAcumulated,
)
from apps.dashboards.domain.entities.country_topics_year import CountryTopicsYear
from apps.dashboards.domain.entities.country_year import CountryYear
from apps.dashboards.domain.repositories.country_repository import CountryRepository


def _get_one(queryset):
    """populate_service.populate() drops each collection and reinserts it in
    one go, but isn't guarded against two overlapping runs (e.g. the
    PopulateView unauthenticated-access window before it required admin
    auth) -- a race there can leave duplicate docs for the same key. A plain
    .get() raises MultipleObjectsReturned in that case, same as every other
    unexpected error -- view callers 500 either way, so only short-circuit
    the duplicate case; a genuinely missing doc still raises DoesNotExist
    exactly like .get() would, preserving existing "year not found" 500s."""
    try:
        return queryset.get()
    except queryset._document.MultipleObjectsReturned:
        return queryset.order_by("-id").first()


class CountryService(CountryRepository):
    def get_year_info(self, year):
        return _get_one(CountryYear.objects.filter(year=year))

    def get_range_info(self, year):
        return CountryYear.objects.filter(year__gt=1999, year__lte=year).order_by(
            "year"
        )

    def get_year(self, year):
        return _get_one(CountryYear.objects.filter(year=year))

    def get_acumulated_by_year(self, year):
        return _get_one(CountryAcumulated.objects.filter(year=year))

    def get_topics_by_year(self, topic, year):
        return _get_one(
            CountryTopicsYear.objects.filter(topic_name=topic, year=year)
        )

    def get_topics_acumulated_by_year(self, topic, year):
        return CountryTopicsAcumulated.objects(topic_name=topic, year=year)

    def get_topics(self, number_top):
        return (
            CountryTopics.objects()
            .filter(topic_name__ne=" ")
            .filter(topic_name__ne="")
            .order_by("-total_articles")[: int(number_top)]
        )

    def get_top_topics(self, year):
        top_topics = (
            CountryTopicsAcumulated.objects(year=year)
            .filter(topic_name__ne=" ")
            .filter(topic_name__ne="")
            .filter(topic_name__ne="")
            .order_by("-total_articles")[:10]
        )
        return top_topics

    def get_last_years(self):
        country_years = CountryYear.objects.filter(year__gt=1999).order_by("year")
        return country_years

    def get_top_topics_by_year(self, year):
        topics_year = (
            CountryTopicsYear.objects(year=year)
            .filter(topic_name__ne=" ")
            .filter(topic_name__ne="")
            .order_by("-total_articles")[:30]
        )
        return topics_year
