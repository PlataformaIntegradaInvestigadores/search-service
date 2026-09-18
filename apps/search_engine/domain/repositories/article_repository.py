from abc import ABC, abstractmethod


class ArticleRepository(ABC):
    @abstractmethod
    def find_by_id(self, article_id) -> object | None:
        pass

    @abstractmethod
    def save(self, article) -> object:
        pass

    @abstractmethod
    def update(self, article: dict) -> object:
        pass

    @abstractmethod
    def find_all(self, page_number=None, page_size=None) -> list[object]:
        pass

    @abstractmethod
    def find_total_articles(self) -> int:
        pass

    @abstractmethod
    def bulk_create(self, articles: list[dict]) -> list[object]:
        pass

    @abstractmethod
    def find_articles_by_ids(
        self,
        ids: list[str],
        page: int = 1,
        page_size: int = 10,
        order_by_date: bool = True,
    ) -> tuple[list[object], int]:
        pass

    @abstractmethod
    def find_most_relevant_articles_by_topic(self, topic: str):
        pass

    @abstractmethod
    def find_articles_by_filter_years(
        self, filter_type: str, filter_years: list[str], ids: list[str]
    ) -> list[object]:
        pass

    @abstractmethod
    def find_years_by_articles(self, ids: list[str]) -> list[object]:
        pass

    @abstractmethod
    def articles_count(self) -> int:
        pass

    @abstractmethod
    def find_authors_by_article(self, article_id: str) -> list[object]:
        pass

    @abstractmethod
    def find_articles_by_author(self, author_id: str) -> list[object]:
        pass
