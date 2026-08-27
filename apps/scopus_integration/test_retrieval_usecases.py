"""Unitarias de ArticleRetrieval y AuthorRetrieval: construccion de URL desde
url/id y ejecucion contra un ScopusClient mockeado."""

from unittest.mock import MagicMock

from django.test import SimpleTestCase

from apps.scopus_integration.application.usecases.article_retrieval_usecase import (
    ArticleRetrieval,
)
from apps.scopus_integration.application.usecases.author_retrieval_usecase import (
    AuthorRetrieval,
)


class ArticleRetrievalTests(SimpleTestCase):
    def test_url_directa_se_usa_tal_cual(self):
        retrieval = ArticleRetrieval(url="http://x/custom")
        self.assertEqual(retrieval.url, "http://x/custom")

    def test_scopus_id_construye_url_con_view_y_field(self):
        retrieval = ArticleRetrieval(scopus_id="123", view="FULL", field="dc:title")
        self.assertEqual(
            retrieval.url,
            "https://api.elsevier.com/content/abstract/scopus_id/123?view=FULL&field=dc:title",
        )

    def test_sin_url_ni_scopus_id_lanza_value_error(self):
        with self.assertRaises(ValueError):
            ArticleRetrieval()

    def test_url_y_scopus_id_juntos_lanza_value_error(self):
        with self.assertRaises(ValueError):
            ArticleRetrieval(url="http://x", scopus_id="1")

    def test_execute_retorna_abstracts_retrieval_response(self):
        client = MagicMock()
        client.exec_request.return_value = {
            "abstracts-retrieval-response": {"coredata": {}}
        }
        retrieval = ArticleRetrieval(scopus_id="123")

        result = retrieval.execute(client)

        self.assertEqual(result, {"coredata": {}})
        client.exec_request.assert_called_once_with(retrieval.url)


class AuthorRetrievalTests(SimpleTestCase):
    def test_author_id_sin_view_ni_field_no_agrega_query_string(self):
        retrieval = AuthorRetrieval(author_id="789")
        self.assertEqual(
            retrieval.url,
            "https://api.elsevier.com/content/author/author_id/789",
        )

    def test_author_id_con_view_y_field_arma_query_string_valida(self):
        # Regresion: un bug previo concatenaba "&view=" sin un "?" inicial,
        # produciendo una URL invalida (".../789&view=FULL").
        retrieval = AuthorRetrieval(author_id="789", view="FULL", field="eid")
        self.assertEqual(
            retrieval.url,
            "https://api.elsevier.com/content/author/author_id/789?view=FULL&field=eid",
        )

    def test_solo_field_tambien_usa_signo_de_interrogacion(self):
        retrieval = AuthorRetrieval(author_id="789", field="eid")
        self.assertEqual(
            retrieval.url,
            "https://api.elsevier.com/content/author/author_id/789?field=eid",
        )

    def test_sin_url_ni_author_id_lanza_value_error(self):
        with self.assertRaises(ValueError):
            AuthorRetrieval()

    def test_url_y_author_id_juntos_lanza_value_error(self):
        with self.assertRaises(ValueError):
            AuthorRetrieval(url="http://x", author_id="1")

    def test_retrieve_respuesta_simple(self):
        client = MagicMock()
        client.exec_request.return_value = {
            "author-retrieval-response": {"coredata": {}}
        }
        retrieval = AuthorRetrieval(author_id="789")

        retrieval.retrieve(client)

        self.assertEqual(retrieval.result, {"coredata": {}})

    def test_retrieve_respuesta_en_lista(self):
        client = MagicMock()
        client.exec_request.return_value = {
            "author-retrieval-response-list": {
                "author-retrieval-response": [{"coredata": {}}]
            }
        }
        retrieval = AuthorRetrieval(author_id="789", response_list=True)

        retrieval.retrieve(client)

        self.assertEqual(retrieval.result, [{"coredata": {}}])
