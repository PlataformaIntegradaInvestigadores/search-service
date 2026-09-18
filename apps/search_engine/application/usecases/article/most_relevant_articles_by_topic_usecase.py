from typing import Any

from apps.search_engine.domain.repositories.article_repository import ArticleRepository


class MostRelevantArticlesUseCase:
    def __init__(self, article_repository: ArticleRepository):
        self.article_repository = article_repository

    def execute(
        self, topic: str, page: int, size: int
    ) -> tuple[list[dict[str, Any]], list[object]]:
        """Normalize both the current repository result and the legacy Series."""
        results = self.article_repository.find_most_relevant_articles_by_topic(topic)
        ranked_articles: list[dict[str, Any]] = []

        if isinstance(results, list):
            ranked_articles = [
                {
                    "scopus_id": str(article["scopus_id"]),
                    "relevance": float(article.get("relevance", 0.0)),
                }
                for article in results
                if isinstance(article, dict) and article.get("scopus_id") is not None
            ]
        elif hasattr(results, "items"):
            ranked_articles = [
                {"scopus_id": str(scopus_id), "relevance": float(score)}
                for scopus_id, score in results.items()
            ]

        article_ids = [article["scopus_id"] for article in ranked_articles]
        years = self.article_repository.find_years_by_articles(article_ids)

        return ranked_articles, years
