from apps.search_engine.domain.repositories.article_repository import ArticleRepository


class ArticlesBulkCreateUseCase:
    def __init__(self, article_repository: ArticleRepository):
        self.article_repository = article_repository

    def execute(self, articles: list[dict]):
        return self.article_repository.bulk_create(articles)
