import logging

import requests

from apps.scopus_integration.application.services.scopus_client import ScopusClient
from apps.scopus_integration.application.usecases.author_retrieval_usecase import (
    AuthorRetrieval,
)
from apps.search_engine.domain.entities.author import Author
from apps.search_engine.domain.repositories.author_repository import AuthorRepository

logger = logging.getLogger("django")


class UpdateAuthorInformationUseCase:
    def __init__(self, author_repository: AuthorRepository, client: ScopusClient):
        self.author_repository = author_repository
        self.client = client

    def execute(self):
        try:
            authors = self.author_repository.authors_no_updated()
            batch_size = 25
            total_authors = len(authors)

            logger.info(f"Updating {total_authors} authors")

            for i in range(0, total_authors, batch_size):
                batch_authors = authors[i : i + batch_size]
                author_retrievals = [
                    AuthorRetrieval(
                        author_id=author_instance.scopus_id, response_list=True
                    )
                    for author_instance in batch_authors
                ]

                for retrieval in author_retrievals:
                    try:
                        retrieval.retrieve(self.client)
                    except requests.HTTPError as e:
                        raise e
                    except Exception as e:
                        raise e

                for author_instance, retrieval in zip(
                    batch_authors, author_retrievals, strict=False
                ):
                    try:
                        retrieval_info = retrieval.result[0]
                        Author.update_from_json(author_data=retrieval_info)
                    except Exception as e:
                        print(f"Error updating author {author_instance.scopus_id}: {e}")
                        raise Exception(
                            f"Error updating author {author_instance.scopus_id}: {e}"
                        )

            return total_authors
        except requests.HTTPError as e:
            raise e
        except Exception as e:
            raise Exception("Error during execution: " + str(e))
