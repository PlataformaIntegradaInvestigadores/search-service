from abc import ABC, abstractmethod


class AuthorRepository(ABC):
    @abstractmethod
    def find_by_id(self, scopus_id) -> object:
        pass

    @abstractmethod
    def find_all(self, page_size=None, page=None) -> (list[object], int):
        pass

    @abstractmethod
    def save(self, author: object) -> object:
        pass

    @abstractmethod
    def update(self, author: object) -> object:
        pass

    @abstractmethod
    def bulk_create(self, authors: list[object]) -> list[object]:
        pass

    @abstractmethod
    def find_authors_by_query(
        self, name: str, page_size=None, page=None
    ) -> list[object]:
        pass

    @abstractmethod
    def find_authors_by_affiliation_filter(
        self, filter_type: str, affiliations_ids: list[str], authors_ids: list[str]
    ) -> list[object]:
        pass

    @abstractmethod
    def find_community(self, authors_ids: list[str]):
        pass

    @abstractmethod
    def find_most_relevant_authors_by_topic(self, topic: str, authors_number: int):
        pass

    @abstractmethod
    def authors_count(self) -> int:
        pass

    @abstractmethod
    def get_authors_no_updated_count(self) -> int:
        pass

    @abstractmethod
    def authors_no_updated(self) -> list[object]:
        pass
