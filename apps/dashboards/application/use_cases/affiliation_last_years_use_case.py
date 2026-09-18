from apps.dashboards.application.services.affiliation_service import AffiliationService


class AffiliationLastYearsUseCase:
    def __init__(self, affiliation_service: AffiliationService):
        self.affiliation_service = affiliation_service

    def execute(self, scopus_id):
        return self.affiliation_service.get_last_years(scopus_id=scopus_id)
