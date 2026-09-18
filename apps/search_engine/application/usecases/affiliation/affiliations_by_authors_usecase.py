from apps.search_engine.domain.repositories.affiliation_repository import (
    AffiliationRepository,
)


class AffiliationByAuthorsUsecase:
    def __init__(self, repository: AffiliationRepository):
        self.repository = repository

    def execute(self, authors: list[str]) -> list[object]:
        return self.repository.find_affiliations_by_authors(authors)
