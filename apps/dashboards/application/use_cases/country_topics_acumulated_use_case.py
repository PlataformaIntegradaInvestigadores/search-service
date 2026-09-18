from apps.dashboards.application.services.country_service import CountryService


class CountryTopicsAcumulatedUseCase:
    def __init__(self, country_service: CountryService):
        self.country_service = country_service

    def execute(self, topic, year):
        return self.country_service.get_topics_acumulated_by_year(
            topic=topic, year=year
        )
