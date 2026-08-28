from apps.dashboards.domain.entities.country_acumulated import CountryAcumulated
from apps.dashboards.domain.entities.country_topics import CountryTopics
from apps.dashboards.domain.entities.country_topics_acumulated import (
    CountryTopicsAcumulated,
)
from apps.dashboards.domain.entities.country_topics_year import CountryTopicsYear
from apps.dashboards.domain.entities.country_year import CountryYear
from apps.dashboards.domain.repositories.country_repository import CountryRepository


class CountryService(CountryRepository):
    def get_year_info(self, year):
        return CountryYear.objects.get(year=year)

    def get_range_info(self, year):
        return CountryYear.objects.filter(year__gt=1999, year__lte=year).order_by(
            "year"
        )

    def get_year(self, year):
        return CountryYear.objects.get(year=year)

    def get_acumulated_by_year(self, year):
        return CountryAcumulated.objects.get(year=year)

    def get_topics_by_year(self, topic, year):
        return CountryTopicsYear.objects.get(topic_name=topic, year=year)

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
