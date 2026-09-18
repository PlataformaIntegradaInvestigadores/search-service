import logging

from django_neomodel import DjangoNode
from neomodel import (
    IntegerProperty,
    RelationshipTo,
    StringProperty,
    UniqueIdProperty,
    db,
)

from apps.search_engine.domain.entities.affiliation import Affiliation
from apps.search_engine.domain.entities.author import Author
from apps.search_engine.domain.entities.topic import Topic

logger = logging.getLogger("django")


class Article(DjangoNode):
    scopus_id = UniqueIdProperty()
    title = StringProperty()
    abstract = StringProperty()
    doi = StringProperty()
    publication_date = StringProperty()
    author_count = IntegerProperty()
    affiliation_count = IntegerProperty()
    corpus = StringProperty()
    affiliations = RelationshipTo(Affiliation, "BELONGS_TO")
    topics = RelationshipTo(Topic, "USES")

    def __str__(self):
        return self.title

    class Meta:
        app_label = "search_engine"

    @classmethod
    @db.transaction
    def from_json(cls, article_data, client) -> "Article":
        scopus_id = cls.validate_scopus_id(article_data.get("dc:identifier", ""))
        if scopus_id is None:
            logger.log(logging.ERROR, "Invalid scopus_id on article creation")
            raise ValueError("Invalid scopus_id on article creation")

        try:
            article = cls.nodes.get(scopus_id=scopus_id)
            logger.info(
                "Article already exists, returning it without further processing"
            )
            return (
                article  # Article already exists, return it without further processing
            )
        except cls.DoesNotExist:
            logger.info(f"Article does not exist, creating it {scopus_id}")
            article_data_processed = {
                "title": article_data.get("dc:title", ""),
                "doi": (
                    article_data.get("prism:doi", "")
                    if article_data.get("prism:doi", "")
                    else None
                ),
                "publication_date": article_data.get("prism:coverDate", ""),
                "abstract": article_data.get("dc:description", ""),
                "author_count": len(article_data.get("author", [])),
                "affiliation_count": len(article_data.get("affiliation", [])),
                "scopus_id": scopus_id,
            }
            article = cls(**article_data_processed).save()

            # Process topics (keywords)
            keywords = article_data.get("authkeywords", "").split(" | ")
            for keyword in keywords:
                keyword_instance = Topic.from_json(keyword)
                if not article.topics.is_connected(keyword_instance):
                    article.topics.connect(keyword_instance)

            # Process affiliations
            affiliations = article_data.get("affiliation", [])
            for affiliation_data in affiliations:
                affiliation_instance = Affiliation.from_dict(affiliation_data)
                if not article.affiliations.is_connected(affiliation_instance):
                    article.affiliations.connect(affiliation_instance)

            print("Iniciando procesamiento de autores")
            logger.log(logging.INFO, "Starting author processing")
            # Process authors
            authors = article_data.get("author", [])

            author_instances = [Author.from_dict(author) for author in authors]
            order = 1
            for author_instance in author_instances:
                # Changed here
                if not author_instance.articles.is_connected(article):
                    author_instance.articles.connect(article, {"order": order})
                order = order + 1
            logger.log(logging.INFO, "Starting co-author processing")
            # Build CoAuthored relationships
            for i, author_instance in enumerate(author_instances):
                for j in range(i + 1, len(author_instances)):
                    co_author_instance = author_instances[j]

                    if author_instance.co_authors.is_connected(co_author_instance):
                        coauth_relationship = author_instance.co_authors.relationship(
                            co_author_instance
                        )
                        coauth_relationship.collab_strength = (
                            cls.calculate_collab_strength(
                                coauth_relationship.shared_pubs + 1,
                                len(author_instance.articles.all()),
                                len(co_author_instance.articles.all()),
                            )
                        )
                        coauth_relationship.shared_pubs += 1
                        coauth_relationship.save()
                    else:
                        coauth_relationship = author_instance.co_authors.connect(
                            co_author_instance,
                            {"collab_strength": 1.0, "shared_pubs": 1},
                        )
                        coauth_relationship.save()
                        print(
                            f"Created relationship strength: {coauth_relationship.collab_strength}"
                        )

        return article

    @staticmethod
    def validate_scopus_id(scopus_id) -> str or None:
        if scopus_id:
            try:
                scopus_id = scopus_id.split(":")[1]
                return scopus_id
            except ValueError:
                return None
        else:
            return None

    @staticmethod
    def calculate_collab_strength(shared_pubs, total_pubs_a, total_pubs_b) -> int:
        return shared_pubs / (total_pubs_a * total_pubs_b) ** 0.5
