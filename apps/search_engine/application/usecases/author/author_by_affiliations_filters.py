from apps.search_engine.domain.repositories.author_repository import AuthorRepository


class AuthorsByAffiliationsFiltersUseCase:

    def __init__(self, author_repository: AuthorRepository):
        self.author_repository = author_repository

    def execute(self, filter_type: str, affiliations_ids: list, authors_ids: list):
        return self.author_repository.find_authors_by_affiliation_filter(
            filter_type, affiliations_ids, authors_ids
        )
