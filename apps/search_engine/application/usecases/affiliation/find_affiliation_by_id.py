from apps.search_engine.domain.repositories.affiliation_repository import (
    AffiliationRepository,
)


class FindAffiliationByScopusIdIUseCase:
    def __init__(self, affiliation_repository: AffiliationRepository):
        self.affiliation_repository = affiliation_repository

    def execute(self, scopus_id: str):
        return self.affiliation_repository.find_by_id(scopus_id)
