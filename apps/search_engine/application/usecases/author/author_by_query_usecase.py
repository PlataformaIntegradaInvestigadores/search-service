from apps.search_engine.domain.repositories.author_repository import AuthorRepository


class AuthorByQueryUseCase:
    def __init__(self, author_repository: AuthorRepository):
        self.author_repository = author_repository

    def execute(self, name: str, page_size=10, page=1) -> list[object]:
        return self.author_repository.find_authors_by_query(
            name, page_size=page_size, page=page
        )
