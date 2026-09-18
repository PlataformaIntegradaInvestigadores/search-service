from apps.dashboards.application.services.affiliation_service import AffiliationService


class AffiliationsAcumulatedUseCase:
    def __init__(self, affiliations_service: AffiliationService):
        self.affiliations_service = affiliations_service

    def execute(self, year):
        return self.affiliations_service.get_top_affiliations_acumulated(year=year)
