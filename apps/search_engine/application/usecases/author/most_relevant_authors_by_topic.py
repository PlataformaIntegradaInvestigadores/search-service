from apps.search_engine.domain.repositories.author_repository import AuthorRepository


class MostRelevantAuthorsByTopicUseCase:
    def __init__(self, repository: AuthorRepository):
        self.repository = repository

    def execute(self, topic: str, authors_number: int):
        return self.repository.find_most_relevant_authors_by_topic(
            topic, authors_number
        )
