from apps.search_engine.domain.repositories.author_repository import AuthorRepository


class AuthorByIdUseCase:
    def __init__(self, author_repository: AuthorRepository):
        self.author_repository = author_repository

    def execute(self, author_id):
        return self.author_repository.find_by_id(author_id)
