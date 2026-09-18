import re

from django_neomodel import DjangoNode
from neomodel import StringProperty
from unidecode import unidecode


class Topic(DjangoNode):
    name = StringProperty(unique_index=True)

    class Meta:
        app_label = "search_engine"

    @classmethod
    def from_json(cls, topic):
        try:
            topic = cls.clean_topic(topic)
            topic_instance = cls.nodes.get(name=topic)
        except cls.DoesNotExist:
            topic_instance = cls(name=topic).save()
        return topic_instance

    @classmethod
    def clean_topic(cls, topic: str) -> str:
        topic = topic.lower()
        topic = unidecode(topic)
        topic = topic.strip()
        topic = re.sub(r"[^a-zA-Z0-9\s]", "", topic)
        return topic
