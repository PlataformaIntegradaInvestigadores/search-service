from apps.search_engine.domain.repositories.topic_repository import TopicRepository


class ListAllTopicsUseCase:
    def __init__(self, topic_repository: TopicRepository):
        self.topic_repository = topic_repository

    def execute(self):
        return self.topic_repository.find_all()
