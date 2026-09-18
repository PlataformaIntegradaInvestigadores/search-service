from abc import ABC, abstractmethod


class TopicRepository(ABC):
    @abstractmethod
    def find_by_id(self, topic_id) -> object:
        pass

    @abstractmethod
    def find_by_article_id(self, article_id) -> list[object]:
        pass

    @abstractmethod
    def find_by_author_id(self, author_id) -> list[object]:
        pass

    @abstractmethod
    def save(self, topic) -> object:
        pass

    @abstractmethod
    def update(self, topic) -> object:
        pass

    @abstractmethod
    def find_all(self) -> list[object]:
        pass

    @abstractmethod
    def topics_count(self) -> int:
        pass
