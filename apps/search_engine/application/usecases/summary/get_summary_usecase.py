from apps.search_engine.domain.repositories.article_repository import ArticleRepository
from apps.search_engine.domain.repositories.author_repository import AuthorRepository
from apps.search_engine.domain.repositories.topic_repository import TopicRepository


class GetSummaryUseCase:
    def __init__(
        self,
        article_repository: ArticleRepository,
        author_repository: AuthorRepository,
        topic_repository: TopicRepository,
    ):
        self.article_repository = article_repository
        self.author_repository = author_repository
        self.topic_repository = topic_repository

    def execute(self) -> dict:
        authors = self.author_repository.authors_count()
        topics = self.topic_repository.topics_count()
        articles = self.article_repository.articles_count()
        return {"authors": authors, "topics": topics, "articles": articles}
