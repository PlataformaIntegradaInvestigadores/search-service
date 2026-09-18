"""Unitarias de: SearchAffiliationRepository (paginacion via cursor de
Scopus + persistencia de CursorReference en Neo4j), ScopusIntegrationUseCase,
UpdateAuthorInformationUseCase, RetrieveScopusData y GenerateCorpusUseCase."""

from unittest.mock import MagicMock, patch

import requests
from django.test import SimpleTestCase, TestCase

from apps.scopus_integration.application.services.search_scopus_service import (
    RetrieveScopusData,
)
from apps.scopus_integration.application.usecases.generate_corpus_usecase import (
    GenerateCorpusUseCase,
)
from apps.scopus_integration.application.usecases.scopus_integration_usecase import (
    ScopusIntegrationUseCase,
)
from apps.scopus_integration.application.usecases.update_author_information_usecase import (
    UpdateAuthorInformationUseCase,
)
from apps.scopus_integration.domain.entities.cursor_reference import CursorReference
from apps.scopus_integration.domain.repositories.search_affiliations_repository import (
    SearchAffiliationRepository,
)


class SearchAffiliationRepositoryInitTests(SimpleTestCase):
    def test_url_directa(self):
        repo = SearchAffiliationRepository(url="http://x")
        self.assertEqual(repo.url, "http://x")

    def test_query_sin_search_type_lanza_value_error(self):
        with self.assertRaises(ValueError):
            SearchAffiliationRepository(url=None, query="AFFIL(...)")

    def test_sin_url_ni_query_lanza_value_error(self):
        with self.assertRaises(ValueError):
            SearchAffiliationRepository(url=None)

    def test_url_y_query_juntos_lanza_value_error(self):
        with self.assertRaises(ValueError):
            SearchAffiliationRepository(url="http://x", query="y")

    def test_query_arma_url_completa(self):
        repo = SearchAffiliationRepository(
            url=None,
            query="Ecuador",
            searchType="scopus",
            view="COMPLETE",
            field="dc:title",
            facets="affiliation-country",
        )
        self.assertIn("query=Ecuador", repo.url)
        self.assertIn("&view=COMPLETE", repo.url)
        self.assertIn("&field=dc:title", repo.url)
        self.assertIn("&facets=affiliation-country", repo.url)


class SearchAffiliationRepositoryRetrieveTests(TestCase):
    """Usa el contenedor real de Neo4j de pruebas para CursorReference."""

    def setUp(self):
        for node in CursorReference.nodes.all():
            node.delete()

    def tearDown(self):
        for node in CursorReference.nodes.all():
            node.delete()

    def test_sin_paginacion_retorna_resultados_de_la_primera_pagina(self):
        client = MagicMock()
        client.exec_request.return_value = {
            "search-results": {
                "opensearch:totalResults": "2",
                "entry": [{"dc:identifier": "SCOPUS_ID:1"}],
            }
        }
        repo = SearchAffiliationRepository(url="http://x")

        results = repo.retrieve(client=client, get_all=False)

        self.assertEqual(results, [{"dc:identifier": "SCOPUS_ID:1"}])
        self.assertEqual(repo.num_res, 1)
        self.assertEqual(repo.tot_num_res, 2)

    def test_falta_search_results_lanza_value_error(self):
        client = MagicMock()
        client.exec_request.return_value = {}
        repo = SearchAffiliationRepository(url="http://x")

        with self.assertRaises(ValueError):
            repo.retrieve(client=client)

    def test_http_error_se_repropaga(self):
        client = MagicMock()
        client.exec_request.side_effect = requests.HTTPError("boom")
        repo = SearchAffiliationRepository(url="http://x")

        with self.assertRaises(requests.HTTPError):
            repo.retrieve(client=client)

    def test_get_all_pagina_hasta_completar_y_crea_cursor(self):
        first_page = {
            "search-results": {
                "opensearch:totalResults": "2",
                "entry": [{"dc:identifier": "SCOPUS_ID:1"}],
                "cursor": {"@next": "cursor-1"},
                "link": [{"@ref": "next", "@href": "http://x/next"}],
            }
        }
        second_page = {
            "search-results": {
                "entry": [{"dc:identifier": "SCOPUS_ID:2"}],
            }
        }
        client = MagicMock()
        client.exec_request.side_effect = [first_page, second_page]

        with patch(
            "apps.scopus_integration.domain.repositories."
            "search_affiliations_repository.Article"
        ) as mock_article:
            mock_article.validate_scopus_id.return_value = "2"
            repo = SearchAffiliationRepository(url="http://x")
            results = repo.retrieve(client=client, get_all=True)

        self.assertEqual(len(results), 2)
        self.assertEqual(CursorReference.nodes.all()[0].cursor, "cursor-1")


class ScopusIntegrationUseCaseTests(SimpleTestCase):
    def test_execute_delega_en_search_affiliation_repository(self):
        client = MagicMock()
        with patch(
            "apps.scopus_integration.application.usecases."
            "scopus_integration_usecase.SearchAffiliationRepository"
        ) as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.retrieve.return_value = [1, 2, 3]
            mock_repo_cls.return_value = mock_repo

            usecase = ScopusIntegrationUseCase(scopus_client=client)
            usecase.execute()

            mock_repo.retrieve.assert_called_once_with(client=client, get_all=True)
            self.assertIs(usecase.search_affiliation_repository, mock_repo)


class UpdateAuthorInformationUseCaseTests(SimpleTestCase):
    def test_actualiza_cada_autor_en_lotes(self):
        author1 = MagicMock(scopus_id="1")
        author2 = MagicMock(scopus_id="2")
        author_repository = MagicMock()
        author_repository.authors_no_updated.return_value = [author1, author2]
        client = MagicMock()

        with patch(
            "apps.scopus_integration.application.usecases."
            "update_author_information_usecase.AuthorRetrieval"
        ) as mock_retrieval_cls, patch(
            "apps.scopus_integration.application.usecases."
            "update_author_information_usecase.Author"
        ) as mock_author:
            mock_retrieval = MagicMock()
            mock_retrieval.result = [{"coredata": {}}]
            mock_retrieval_cls.return_value = mock_retrieval

            usecase = UpdateAuthorInformationUseCase(
                author_repository=author_repository, client=client
            )
            total = usecase.execute()

        self.assertEqual(total, 2)
        self.assertEqual(mock_author.update_from_json.call_count, 2)
        mock_retrieval_cls.assert_called_with(author_id="2", response_list=True)

    def test_error_en_retrieve_se_repropaga(self):
        author_repository = MagicMock()
        author_repository.authors_no_updated.return_value = [MagicMock(scopus_id="1")]
        client = MagicMock()

        with patch(
            "apps.scopus_integration.application.usecases."
            "update_author_information_usecase.AuthorRetrieval"
        ) as mock_retrieval_cls:
            mock_retrieval = MagicMock()
            mock_retrieval.retrieve.side_effect = requests.HTTPError("boom")
            mock_retrieval_cls.return_value = mock_retrieval

            usecase = UpdateAuthorInformationUseCase(
                author_repository=author_repository, client=client
            )
            with self.assertRaises(requests.HTTPError):
                usecase.execute()


class RetrieveScopusDataTests(SimpleTestCase):
    def test_retrieve_data_delega_en_custom_request(self):
        with patch(
            "apps.scopus_integration.application.services."
            "search_scopus_service.CustomRequest"
        ) as mock_request_cls:
            mock_request = MagicMock()
            mock_request.do_get.return_value = {"search-results": {}}
            mock_request_cls.return_value = mock_request

            service = RetrieveScopusData()
            result = service.retrieve_data()

        self.assertEqual(result, {"search-results": {}})

    def test_get_total_articles_extrae_total_results(self):
        service = RetrieveScopusData()
        service.retrieve_data = MagicMock(
            return_value={
                "search-results": {"opensearch:totalResults": "42"},
            }
        )

        self.assertEqual(service.get_total_articles_from_scopus(), "42")

    def test_get_total_articles_error_se_envuelve(self):
        service = RetrieveScopusData()
        service.retrieve_data = MagicMock(side_effect=RuntimeError("boom"))

        with self.assertRaises(Exception) as ctx:
            service.get_total_articles_from_scopus()

        self.assertIn("Error getting total articles", str(ctx.exception))


class GenerateCorpusUseCaseTests(SimpleTestCase):
    def test_execute_delega_en_corpus_service(self):
        corpus_service = MagicMock()
        corpus_service.get_combined_corpus.return_value = [{"doc_id": "1"}]

        usecase = GenerateCorpusUseCase(corpus_service=corpus_service)
        result = usecase.execute()

        self.assertEqual(result, [{"doc_id": "1"}])

    def test_error_se_envuelve(self):
        corpus_service = MagicMock()
        corpus_service.get_combined_corpus.side_effect = RuntimeError("boom")

        usecase = GenerateCorpusUseCase(corpus_service=corpus_service)
        with self.assertRaises(Exception):
            usecase.execute()
