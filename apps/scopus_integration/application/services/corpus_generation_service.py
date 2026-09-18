from neomodel import db

from apps.scopus_integration.domain.repositories.corpus_repository import (
    CorpusRepository,
)


class CorpusService(CorpusRepository):
    def get_corpus_by_author(self):
        try:
            query = """match (au:Author)-[:WROTE]->(ar:Article) optional match (ar)-[r:USES]-(
            to:Topic) return au.scopus_id, collect(distinct([ar.title, ar.abstract])) as articles, collect(to.name) 
            as topics"""

            results, meta = db.cypher_query(query)

            authors_with_articles_and_topics = []
            for scopus_id, articles, topics in results:
                articles_list = [
                    {"title": article[0], "abstract": article[1]}
                    for article in articles
                ]
                authors_with_articles_and_topics.append(
                    {
                        "scopus_id": scopus_id,
                        "articles": articles_list,
                        "topics": topics,
                    }
                )

            return authors_with_articles_and_topics
        except Exception as e:
            raise Exception("Error while getting corpus by author ", str(e))

    def get_corpus_by_article(self):
        try:
            query = """
               MATCH (ar:Article)
               OPTIONAL MATCH (ar)-[:USES]-(to:Topic)
               RETURN ar.scopus_id as scopus_id, ar.title as title, ar.abstract as abstract, collect(to.name) as topics
               """
            results, meta = db.cypher_query(query)

            articles_with_topics = []
            for scopus_id, title, abstract, topics in results:
                articles_with_topics.append(
                    {
                        "scopus_id": scopus_id,
                        "title": title,
                        "abstract": abstract,
                        "topics": topics,
                    }
                )

            return articles_with_topics
        except Exception as e:
            raise Exception("Error while getting corpus by article ", str(e))

    def get_combined_corpus(self):
        try:
            authors_data = self.get_corpus_by_author()
            articles_data = self.get_corpus_by_article()

            # Helper function to handle None values
            def safe_str(value):
                return value if value is not None else ""

            # Combine authors+articles data
            combined_data = []
            for item in articles_data:
                article = {
                    "doc_id": safe_str(item["scopus_id"]),
                    "doc": (
                        safe_str(item["title"])
                        + " "
                        + safe_str(item["abstract"])
                        + " "
                        + " ".join(safe_str(topic) for topic in item["topics"])
                    ).strip(),
                }
                combined_data.append(article)

            for item in authors_data:
                articles = [
                    " ".join(safe_str(article_part) for article_part in article)
                    for article in item["articles"]
                ]
                author = {
                    "doc_id": safe_str(item["scopus_id"]),
                    "doc": (
                        " ".join(articles)
                        + " "
                        + " ".join(safe_str(topic) for topic in item["topics"])
                    ).strip(),
                }
                combined_data.append(author)

            return combined_data
        except Exception as e:
            raise Exception("Error while generating corpus ", str(e))
