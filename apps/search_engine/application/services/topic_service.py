from neomodel import db

from apps.search_engine.domain.entities.topic import Topic
from apps.search_engine.domain.repositories.topic_repository import TopicRepository


class TopicService(TopicRepository):
    def find_by_id(self, topic_id) -> Topic:
        pass

    def find_by_article_id(self, article_id) -> list[Topic]:
        pass

    def find_by_author_id(self, author_id) -> list[Topic]:
        pass

    def save(self, topic) -> Topic:
        pass

    def update(self, topic) -> Topic:
        pass

    def find_all(self) -> list[Topic]:
        return Topic.nodes.all()

    def topics_count(self) -> int:
        try:
            query = "MATCH (n:Topic) RETURN count(n)"

            results, meta = db.cypher_query(query)
            return results[0][0]
        except Exception as e:
            raise Exception(e)
