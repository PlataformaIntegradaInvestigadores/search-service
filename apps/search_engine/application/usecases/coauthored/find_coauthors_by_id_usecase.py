from apps.search_engine.domain.repositories.coauthored_repository import (
    CoAuthoredRepository,
)


class FindCoauthorsByIdUsecase:
    def __init__(self, coauthor_repository: CoAuthoredRepository):
        self.coauthor_repository = coauthor_repository

    def execute(self, author_id):
        return self.coauthor_repository.find_coauthors_by_id(author_id)
