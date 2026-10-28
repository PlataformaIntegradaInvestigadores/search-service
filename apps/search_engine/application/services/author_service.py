import pandas as pd
from neomodel import Q, db
from unidecode import unidecode

from apps.search_engine.application.utils.tfidf import Model
from apps.search_engine.domain.entities.author import Author
from apps.search_engine.domain.repositories.author_repository import AuthorRepository


class AuthorService(AuthorRepository):

    def authors_no_updated(self) -> list[object]:
        try:
            query = "MATCH (a:Author) WHERE a.updated = false RETURN a"
            results, meta = db.cypher_query(query)
            authors = [Author.inflate(row[0]) for row in results]
            return authors
        except Exception as e:
            raise ValueError(f"Error finding authors no updated: {e}")

    def get_authors_no_updated_count(self) -> int:
        try:
            query = "MATCH (a:Author) WHERE a.updated = false RETURN count(a) "
            results, meta = db.cypher_query(query)
            authors_no_updated = results[0][0]
            return authors_no_updated
        except Exception as e:
            raise ValueError(f"Error finding authors no updated count: {e}")

    def authors_count(self) -> int:
        try:
            query = "MATCH (a:Author) RETURN count(a) "
            results, meta = db.cypher_query(query)
            total_authors = results[0][0]
            return total_authors
        except Exception as e:
            raise ValueError(f"Error finding total authors: {e}")

    def find_most_relevant_authors_by_topic(self, topic: str, authors_number: int):
        try:
            m = Model("author")

            # Primero intentar con la query completa
            authors = m.get_most_relevant_docs_by_topic_v2(topic, authors_number)

            # Si no hay resultados, intentar con términos individuales
            if authors.empty:
                terms = topic.split()
                all_authors = []

                for term in terms:
                    term_authors = m.get_most_relevant_docs_by_topic_v2(
                        term, authors_number
                    )
                    if not term_authors.empty:
                        all_authors.append(term_authors)

                if all_authors:
                    # Combinar resultados de términos individuales
                    combined = pd.concat(all_authors)
                    # Agrupar por autor y sumar scores
                    combined = combined.groupby(combined.index).sum()
                    # Ordenar y limitar
                    authors = combined.sort_values(ascending=False).head(authors_number)

            return authors

        except Exception as e:
            raise Exception(f"Error finding most relevant authors by topic: {e}")

    def find_community(self, authors_ids: list[str]):
        try:
            query = Q(scopus_id__in=authors_ids)
            nodes = Author.nodes.filter(query)
            # Consulta para obtener enlaces
            query_links = """
                  WITH $auth_list as authList
                  MATCH (au1:Author)-[r:CO_AUTHORED]-(au2:Author)
                  WHERE au1.scopus_id IN authList AND au2.scopus_id IN authList AND au1 > au2
                  RETURN collect({source: au1.scopus_id, target: au2.scopus_id,
                      collabStrength: toFloat(r.collab_strength)}) as links
                  """
            result = db.cypher_query(
                query_links, {"auth_list": [str(w) for w in authors_ids]}
            )
            # Ensure we only unpack two values
            result_links, meta = result
            links = result_links[0][0]

            return {
                "nodes": nodes,
                "links": links,
                "size_nodes": len(nodes),
                "size_links": len(links),
            }
        except Exception as e:
            raise Exception(f"Error finding community: {e}")

    def find_authors_by_affiliation_filter(
        self, filter_type: str, affiliations_ids: list[str], authors_ids: list[str]
    ) -> list[object]:
        try:
            print("Filter type: ", filter_type)
            print("Affiliations IDs: ", affiliations_ids)
            print("Authors IDs: ", authors_ids)
            if filter_type == "include":
                query = """
                   MATCH (a:Author)-[:AFFILIATED_WITH]->(aff:Affiliation)
                   WHERE a.scopus_id IN $authors_ids AND aff.scopus_id IN $affiliations_ids
                   RETURN a
                   """
            else:
                query = """
                   MATCH (a:Author)-[:AFFILIATED_WITH]->(aff:Affiliation)
                   WHERE a.scopus_id IN $authors_ids AND NOT aff.scopus_id IN $affiliations_ids
                   RETURN a
                   """
            results, _ = db.cypher_query(
                query,
                {
                    "authors_ids": [str(w) for w in authors_ids],
                    "affiliations_ids": [str(w) for w in affiliations_ids],
                },
            )
            authors = [Author.inflate(row[0]) for row in results]

            print("Len of authors extracted: ", len(authors))

            return authors

        except Exception as e:
            raise Exception(f"Error finding authors by affiliation filter: {e}")

    def _build_diacritic_regex(self, text: str) -> str:
        mapping = {
            "a": "[aáäâãà]",
            "e": "[eéëêè]",
            "i": "[iíïîì]",
            "o": "[oóöôõò]",
            "u": "[uúüûù]",
        }
        regex_str = ""
        base_text = unidecode(text).strip().lower()
        for char in base_text:
            if char in mapping:
                regex_str += mapping[char]
            else:
                if char in ".^$*+?()[{\\|":
                    regex_str += "\\" + char
                else:
                    regex_str += char
        return f"(?i).*{regex_str}.*"

    def find_authors_by_query(
        self, name: str, page_size=1, page=10
    ) -> (list[object], int):
        custom_name = self._build_diacritic_regex(name)
        skip = (page - 1) * page_size

        query_count = """
                MATCH (au:Author) 
                WHERE  au.first_name =~ $pattern or 
                au.last_name =~ $pattern or 
                (au.first_name + " " + au.last_name) =~ $pattern or
                (au.last_name + " " + au.first_name) =~ $pattern or  
                au.auth_name =~ $pattern or 
                au.initials =~ $pattern or 
                au.email =~ $pattern or 
                au.scopus_id =~ $pattern
                RETURN count(au) as total
        """
        results_count, meta = db.cypher_query(query_count, {"pattern": custom_name})
        total = results_count[0][0]

        query_fetch = """
                MATCH (au:Author) 
                WHERE  au.first_name =~ $pattern or 
                au.last_name =~ $pattern or 
                (au.first_name + " " + au.last_name) =~ $pattern or
                (au.last_name + " " + au.first_name) =~ $pattern or  
                au.auth_name =~ $pattern or 
                au.initials =~ $pattern or 
                au.email =~ $pattern or 
                au.scopus_id =~ $pattern
                RETURN au
                ORDER BY au.citation_count DESC
                SKIP $skip LIMIT $limit
                """
        results_fetch, meta = db.cypher_query(
            query_fetch,
            {"pattern": custom_name, "skip": int(skip), "limit": int(page_size)},
        )
        authors = [Author.inflate(row[0]) for row in results_fetch]
        return authors, total

    def find_all(self, page_size=None, page=None) -> list[Author]:
        try:
            skip = (page - 1) * page_size
            query = "MATCH (a:Author) RETURN a SKIP $skip LIMIT $limit"
            results, meta = db.cypher_query(
                query, {"skip": int(skip), "limit": int(page_size)}
            )
            authors = [Author.inflate(row[0]) for row in results]
            return authors
        except Exception as e:
            raise Exception(f"Error finding all authors: {e}")

    def find_by_id(self, scopus_id) -> Author:
        try:
            return Author.nodes.get(scopus_id=scopus_id)
        except Exception as e:
            raise Exception(f"Error finding author by id: {e}")

    def save(self, author) -> Author:
        pass

    def update(self, author) -> Author:
        pass

    def bulk_create(self, authors: list[dict]) -> list[Author]:
        try:
            return Author.get_or_create(*authors)
        except Exception as e:
            raise Exception(f"Error bulk creating authors: {e}")
