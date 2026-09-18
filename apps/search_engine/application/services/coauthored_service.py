from neomodel import DoesNotExist, db

from apps.search_engine.domain.repositories.author_repository import AuthorRepository
from apps.search_engine.domain.repositories.coauthored_repository import (
    CoAuthoredRepository,
)


class CoAuthoredService(CoAuthoredRepository):
    def __init__(self, author_repository: AuthorRepository):
        self.author_repository = author_repository

    def save(self, coauthored) -> object:
        pass

    def find_coauthors_by_id(self, author_id: str):
        try:
            author = self.author_repository.find_by_id(author_id)
            nodes = (
                list(author.co_authors.all())
                if hasattr(author.co_authors, "all")
                else list(author.co_authors)
            )

            # Recogemos los IDs del autor principal y todos sus coautores
            all_scopus_ids = [str(author.scopus_id)] + [str(c.scopus_id) for c in nodes]
            auth_list_str = ", ".join([f'"{sid}"' for sid in all_scopus_ids])

            # Consulta Cypher para obtener TODAS las aristas de coautoría entre cualquier par de nodos en la red (Densidad de red)
            query_links = f"""
                WITH [{auth_list_str}] as authList
                MATCH (au1:Author)-[r:CO_AUTHORED]-(au2:Author)
                WHERE au1.scopus_id IN authList AND au2.scopus_id IN authList AND au1.scopus_id > au2.scopus_id
                RETURN collect({{
                    source: au1.scopus_id, 
                    target: au2.scopus_id, 
                    collabStrength: toFloat(r.collab_strength)
                }}) as links
            """
            result, _ = db.cypher_query(query_links)
            links = []
            if result and result[0] and result[0][0]:
                for item in result[0][0]:
                    links.append(
                        {
                            "source": int(item["source"]),
                            "target": int(item["target"]),
                            "collabStrength": float(item["collabStrength"]),
                        }
                    )

            return nodes, links
        except DoesNotExist as e:
            raise e
        except Exception as e:
            raise Exception(
                "An error occurred while trying to find coauthors by id.", str(e)
            )
