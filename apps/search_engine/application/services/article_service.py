from neomodel import db

from apps.search_engine.application.utils.tfidf import Model
from apps.search_engine.domain.entities.article import Article
from apps.search_engine.domain.repositories.article_repository import ArticleRepository


class ArticleService(ArticleRepository):
    def find_articles_by_author(self, author_id: str) -> list[object]:
        try:
            query = "MATCH (a:Article)-[:WROTE]-(au:Author) WHERE au.scopus_id = $author_id RETURN a"
            results, meta = db.cypher_query(query, {"author_id": author_id})
            articles = [Article.inflate(row[0]) for row in results]
            return articles
        except Exception as e:
            raise Exception(f"Error finding articles by author: {e}")

    def articles_count(self) -> int:
        try:
            query = "MATCH (a:Article) RETURN count(a) "
            results, meta = db.cypher_query(query)
            total_articles = results[0][0]
            return total_articles
        except Exception as e:
            raise ValueError(f"Error finding total articles: {e}")

    def find_articles_by_ids(
        self,
        ids: list[str],
        page: int = 1,
        page_size: int = 10,
        order_by_date: bool = True,
    ) -> tuple[list[object], int]:
        try:
            skip = (page - 1) * page_size
            # Asegúrate de que los IDs estén en el formato correcto
            ids_integer = [str(w) for w in ids]

            # Obtener total de artículos
            query_to_find_articles = f"MATCH (a:Article) WHERE a.scopus_id IN {ids_integer} RETURN count(a) AS total"
            total_results, meta = db.cypher_query(query_to_find_articles)
            total_articles = total_results[0][0]

            # Obtener artículos con toda su información
            order_clause = "ORDER BY a.publication_date DESC" if order_by_date else ""
            query = f"""
                MATCH (a:Article) 
                WHERE a.scopus_id IN {ids_integer} 
                OPTIONAL MATCH (a)-[:WROTE]-(au:Author)
                OPTIONAL MATCH (a)-[:BELONGS_TO]-(aff:Affiliation)
                RETURN a, 
                    count(DISTINCT au) as author_count,
                    count(DISTINCT aff) as affiliation_count,
                    collect(DISTINCT au.auth_name) as authors,
                    collect(DISTINCT aff.name) as affiliations
                {order_clause}
                SKIP {skip} LIMIT {page_size}
            """

            results, meta = db.cypher_query(query)

            # Procesar resultados
            articles = []
            for row in results:
                article = Article.inflate(row[0])
                article_dict = {
                    "scopus_id": article.scopus_id,
                    "title": article.title,
                    "publication_date": article.publication_date,
                    "author_count": row[1],
                    "affiliation_count": row[2],
                    "authors": row[3],
                    "affiliations": row[4],
                }
                articles.append(article_dict)

            return articles, total_articles
        except Exception as e:
            raise Exception(f"Error finding articles by ids: {e}")

    # En article_service.py
    def find_most_relevant_articles_by_topic(self, topic: str):
        try:
            m = Model("article")
            # Devuelve un Series/DataFrame con scopus_id y score sin hacer N+1 queries a la BD
            return m.get_most_relevant_docs_by_topic_v2(topic, None)
        except Exception as e:
            raise Exception(f"Error finding most relevant articles by topic: {e}")

    def find_articles_by_filter_years(
        self, filter_type: str, filter_years: list[str], ids: list[str]
    ) -> list[object]:
        try:
            # Cambiar este cmportamiento dependiendo de la bd

            ids = [f'"{str(w)}"' for w in ids]
            ids_str = ", ".join(map(str, ids))
            filter_years_str = " OR ".join(
                [f'a.publication_date CONTAINS "{year}"' for year in filter_years]
            )

            if filter_type == "include":
                query = f"""
                MATCH (a:Article)
                WHERE a.scopus_id IN [{ids_str}] AND ({filter_years_str})
                RETURN a
                """
            else:
                query = f"""
                MATCH (a:Article)
                WHERE a.scopus_id IN [{ids_str}] AND NOT ({filter_years_str})
                RETURN a
                """
            results, _ = db.cypher_query(query)
            articles = [Article.inflate(row[0]) for row in results]
            return articles
        except Exception as e:
            raise Exception(f"Error finding articles by filter years: {e}")

    def find_years_by_articles(self, ids: list[str]) -> list[object]:
        try:
            # Comment
            query = f"MATCH (a:Article) WHERE a.scopus_id IN {ids} RETURN a"
            results, meta = db.cypher_query(query)
            articles = [Article.inflate(row[0]) for row in results]
            years = []
            for article in articles:
                years.append(article.publication_date)
            return years
        except Exception as e:
            raise Exception(f"Error getting years by articles: {e}")

    def bulk_create(self, articles: list[dict]) -> list[Article]:
        try:
            return Article.get_or_create(*articles)
        except Exception as e:
            raise ValueError(f"Error creating articles: {e}")

    def find_total_articles(self) -> int:
        try:
            query = "MATCH (a:Article) RETURN count(a) AS total"
            results, meta = db.cypher_query(query)
            total_articles = results[0][0]
            return total_articles
        except Exception as e:
            raise ValueError(f"Error finding total articles: {e}")

    def find_all(self, page_number=1, page_size=10) -> list[Article]:
        try:
            skip = (page_number - 1) * page_size
            query = f"MATCH (a:Article) RETURN a SKIP {skip} LIMIT {page_size}"
            results, meta = db.cypher_query(query)
            articles = [Article.inflate(row[0]) for row in results]
            return articles
        except Exception as e:
            raise Exception(f"Error finding all articles: {e}")

    def update(self, article: dict) -> Article:
        try:
            articles = Article.create_or_update(article)
            return articles[0]
        except Exception as e:
            raise Exception(f"Error updating article: {e}")

    def save(self, article) -> Article:
        try:
            article = Article(**article)
            article.save()
            return article
        except Exception as e:
            raise Exception(f"Error saving article: {e}")

    def find_by_id(self, article_id) -> Article | None:
        try:
            article = Article.nodes.get_or_none(scopus_id=article_id)
            return article
        except Exception as e:
            raise Exception(f"Error finding article by id: {e}")

    def find_authors_by_article(self, article_id: str) -> list[object]:
        try:
            query = (
                "MATCH (a:Article {scopus_id: $article_id}) "
                "OPTIONAL MATCH (a)-[:WROTE]-(au:Author) "
                "RETURN collect(DISTINCT {scopusId: au.scopus_id, name: au.auth_name})"
            )
            results, meta = db.cypher_query(query, {"article_id": article_id})
            authors = [row[0] for row in results]
            return authors
        except Exception as e:
            raise Exception(f"Error finding authors by article: {e}")
