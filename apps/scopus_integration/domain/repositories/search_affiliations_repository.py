"""
Created on Mon May 17 2021

@author: Nicolas
updated by: Fernando
"""

import logging
from urllib.parse import quote_plus as url_encode

import requests

from apps.scopus_integration.application.services.scopus_client import ScopusClient
from apps.scopus_integration.domain.entities.cursor_reference import CursorReference
from apps.scopus_integration.utils.utils import encodeFacets
from apps.search_engine.application.services.article_service import ArticleService
from apps.search_engine.domain.entities.article import Article

logger = logging.getLogger("django")


class SearchAffiliationRepository:
    # statics variables
    _url_base = "https://api.elsevier.com/content/search/"
    article_service = ArticleService()

    def __init__(
        self, url, query=None, facets=None, view=None, field=None, searchType=None
    ):
        self.num_res = None
        self.tot_num_res = None
        self.results = None
        self.facets = facets
        if url and not query:
            self.url = url
        elif query and not url:
            if not searchType:
                raise ValueError("Type of search is needed.")
            self.url = self._url_base + searchType + "?query=" + url_encode(query)
            if view:
                self.url = self.url + "&view=" + view
            if field:
                self.url = self.url + "&field=" + field
            if facets:
                self.url = self.url + "&facets=" + facets
        elif not url and not query:
            raise ValueError("URL or query is needed.")
        else:
            raise ValueError(
                "Just one parameter is needed, either the URL or the query. Not both."
            )

    def retrieve(self, client: ScopusClient = None, get_all=False):
        try:
            api_response = client.exec_request(self.url)

            if "search-results" not in api_response:
                raise ValueError("Invalid API response: missing 'search-results'")

            self.tot_num_res = int(
                api_response["search-results"].get("opensearch:totalResults", 0)
            )
            logger.info(f"Total results: {self.tot_num_res}")

            self.results = api_response["search-results"].get("entry", [])
            self.num_res = len(self.results)
            logger.info(f"Current results: {self.num_res}")

            # Check if there are existing cursors
            existing_cursors = {
                reference.cursor for reference in CursorReference.nodes.all()
            }
            logger.info(f"Existing cursors: {len(existing_cursors)}")

            if get_all:
                while self.num_res < self.tot_num_res:
                    cursor_dict = api_response.get("search-results", {}).get(
                        "cursor", {}
                    )
                    cursor = cursor_dict.get("@next") if cursor_dict else None
                    links = api_response.get("search-results", {}).get("link", [])

                    next_urls = [
                        e.get("@href") for e in links if e.get("@ref") == "next"
                    ]
                    next_url = next_urls[0] if next_urls else None

                    logger.info(f"Current results {self.num_res} of {self.tot_num_res}")

                    # If cursor is in existing_cursors, it means that the search was already done
                    if cursor in existing_cursors:
                        while True:
                            if not next_url:
                                logger.info("No more results available.")
                                break

                            try:
                                # Search for the next cursor
                                api_response = client.exec_request(
                                    encodeFacets(next_url, self.facets)
                                )
                            except Exception as e:
                                logger.error(f"API request failed: {e}")
                                raise e

                            cursor_dict = api_response.get("search-results", {}).get(
                                "cursor", {}
                            )
                            cursor = cursor_dict.get("@next") if cursor_dict else None
                            links = api_response.get("search-results", {}).get(
                                "link", []
                            )

                            next_urls = [
                                e.get("@href") for e in links if e.get("@ref") == "next"
                            ]
                            next_url = next_urls[0] if next_urls else None

                            if cursor and cursor not in existing_cursors:
                                break

                            logger.info(f"Cursor {cursor} already exists. Skipping...")
                            self.results += api_response["search-results"].get(
                                "entry", []
                            )
                            self.num_res = len(self.results)
                            logger.info(
                                f"Current results {self.num_res} of {self.tot_num_res}"
                            )

                    api_response = client.exec_request(
                        encodeFacets(next_url, self.facets)
                    )
                    new_entries = api_response["search-results"].get("entry", [])

                    for article_ in new_entries:
                        try:
                            scopus_id = Article.validate_scopus_id(
                                article_.get("dc:identifier", "")
                            )
                        except ValueError as e:
                            logger.error(f"Error on article validation: {e}")
                            raise e
                        else:
                            logger.info(
                                f"Processing article with scopus_id: {scopus_id}"
                            )
                            Article.from_json(article_, client)

                    self.results += new_entries
                    self.num_res = len(self.results)

                    if cursor and cursor not in existing_cursors:
                        try:
                            CursorReference(next_url=next_url, cursor=cursor).save()
                            logger.info(f"Cursor {cursor} created and saved")
                        except Exception as e:
                            logger.error(f"Error on cursor creation: {e}")
                            raise e

            return self.results

        except requests.HTTPError as e:
            logger.error(f"Error on search due to HTTP error: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            raise e
