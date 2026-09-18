from apps.search_engine.domain.repositories.affiliation_repository import (
    AffiliationRepository,
)


class ListAllAffiliationsUseCase:
    def __init__(self, affiliation_repository: AffiliationRepository):
        self.affiliation_repository = affiliation_repository

    def execute(self, page_number=1, page_size=10) -> list[object]:
        return self.affiliation_repository.find_all(
            page_number=page_number, page_size=page_size
        )
