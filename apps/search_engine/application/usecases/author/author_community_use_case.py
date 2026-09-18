from apps.search_engine.domain.repositories.author_repository import AuthorRepository


class AuthorsCommunityUseCase:
    def __init__(self, author_repository: AuthorRepository):
        self.author_repository = author_repository

    def execute(self, authors_ids: list[str]):
        print("Type of authors_ids: ", type(authors_ids))
        return self.author_repository.find_community(authors_ids)
