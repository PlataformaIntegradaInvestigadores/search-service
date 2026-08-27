from apps.search_engine.domain.repositories.author_repository import AuthorRepository


class AuthorsBulkCreateUseCase:
    def __init__(self, author_repository: AuthorRepository):
        self.author_repository = author_repository

    def execute(self, authors: list[dict]):
        return self.author_repository.bulk_create(authors)
