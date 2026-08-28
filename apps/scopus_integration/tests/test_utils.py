"""Unitarias de apps/scopus_integration/utils/utils.py: funciones puras de
transformacion de payloads de la API de Scopus (URL encoding, dataframes,
diccionarios anidados)."""

import numpy as np
import pandas as pd
from django.test import SimpleTestCase

from apps.scopus_integration.utils.utils import (
    affiliation_to_scopus_search,
    article_retrieval_to_scopus_search,
    authorkeywords_to_scopus_search,
    author_to_scopus_search,
    chunker,
    encodeFacets,
    recastDfAffiliations,
    recast_df_articles,
    recast_df_authors,
    rewrite_article_affil_list,
    rewrite_article_authors,
)


class EncodeFacetsTests(SimpleTestCase):
    def test_sin_facets_retorna_url_intacta(self):
        self.assertEqual(encodeFacets("http://x/?a=1", None), "http://x/?a=1")

    def test_reemplaza_facets_decodificado_por_codificado(self):
        url = "http://x/?facets=affiliation-country"
        result = encodeFacets(url, "affiliation-country")
        self.assertEqual(result, url)


class RecastDfAffiliationsTests(SimpleTestCase):
    def test_renombra_y_reformatea_columnas(self):
        df = pd.DataFrame(
            [
                {
                    "@_fa": "true",
                    "prism:url": "http://x",
                    "dc:identifier": "AFFILIATION_ID:60072059",
                    "affiliation-name": "ESPOL",
                    "document-count": "10",
                }
            ]
        )
        recastDfAffiliations(df)
        self.assertNotIn("@_fa", df.columns)
        self.assertNotIn("prism:url", df.columns)
        self.assertEqual(df.loc[0, "identifier"], "60072059")
        self.assertEqual(df.loc[0, "affiliation_name"], "ESPOL")


class RewriteArticleAffilListTests(SimpleTestCase):
    def test_elimina_campos_ruidosos(self):
        affils = [{"@_fa": "true", "affiliation-url": "http://x", "afid": "1"}]
        result = rewrite_article_affil_list(affils)
        self.assertEqual(result, [{"afid": "1"}])


class RewriteArticleAuthorsTests(SimpleTestCase):
    def test_aplana_afid_de_lista_de_dicts_a_lista_de_valores(self):
        authors = [
            {
                "@_fa": "true",
                "author-url": "http://x",
                "afid": [{"$": "111"}, {"$": "222"}],
            }
        ]
        result = rewrite_article_authors(authors)
        self.assertEqual(result[0]["afid"], ["111", "222"])
        self.assertNotIn("@_fa", result[0])
        self.assertNotIn("author-url", result[0])

    def test_sin_afid_asigna_lista_vacia(self):
        authors = [{"@_fa": "true", "author-url": "http://x"}]
        result = rewrite_article_authors(authors)
        self.assertEqual(result[0]["afid"], [])


class RecastDfArticlesTests(SimpleTestCase):
    def test_reestructura_dataframe_completo(self):
        df = pd.DataFrame(
            [
                {
                    "@_fa": "true",
                    "prism:url": "http://x",
                    "dc:identifier": "SCOPUS_ID:123",
                    "dc:title": "Titulo",
                    "prism:coverDate": "2024-01-01",
                    "dc:description": "abstract",
                    "author": [
                        {"@_fa": "true", "author-url": "http://x"},
                    ],
                    "affiliation": [
                        {"@_fa": "true", "affiliation-url": "http://x"},
                    ],
                    "authkeywords": "kw",
                },
                {
                    "@_fa": "true",
                    "prism:url": "http://y",
                    "dc:identifier": "SCOPUS_ID:456",
                    "dc:title": "Titulo2",
                    "prism:coverDate": "2024-02-01",
                    "dc:description": "abstract2",
                    "author": [],
                    "affiliation": np.nan,
                    "authkeywords": "kw2",
                },
            ]
        )
        recast_df_articles(df)

        self.assertEqual(len(df), 1)
        self.assertEqual(df.loc[0, "identifier"], "123")
        self.assertEqual(df.loc[0, "title"], "Titulo")
        self.assertEqual(df.loc[0, "author_count"], 1)
        self.assertEqual(df.loc[0, "affiliation_count"], 1)


class ChunkerTests(SimpleTestCase):
    def test_divide_en_sublistas_del_tamano_dado(self):
        result = list(chunker([1, 2, 3, 4, 5], 2))
        self.assertEqual(result, [[1, 2], [3, 4], [5]])

    def test_lista_vacia_no_produce_chunks(self):
        self.assertEqual(list(chunker([], 3)), [])


class RecastDfAuthorsTests(SimpleTestCase):
    def test_extrae_campos_desde_coredata_y_preferred_name(self):
        df = pd.DataFrame(
            [
                {
                    "@status": "found",
                    "@_fa": "true",
                    "coredata": {
                        "dc:identifier": "AUTHOR_ID:789",
                        "eid": "9-s2.0-789",
                        "orcid": "0000-0000-0000-0001",
                        "document-count": "5",
                    },
                    "preferred-name": {"given-name": "Ana", "surname": "Perez"},
                }
            ]
        )
        recast_df_authors(df)

        self.assertEqual(df.loc[0, "identifier"], "789")
        self.assertEqual(df.loc[0, "eid"], "9-s2.0-789")
        self.assertEqual(df.loc[0, "first_name"], "Ana")
        self.assertEqual(df.loc[0, "last_name"], "Perez")
        self.assertNotIn("coredata", df.columns)
        self.assertNotIn("preferred-name", df.columns)

    def test_campos_faltantes_asumen_nan(self):
        # preferred-name como string (no dict) fuerza la rama np.nan del
        # codigo de produccion (indexar un dict vacio con "given-name" lanza
        # KeyError, esa rama solo protege el caso "no es un dict").
        df = pd.DataFrame(
            [
                {
                    "@status": "found",
                    "@_fa": "true",
                    "coredata": {},
                    "preferred-name": "no-disponible",
                }
            ]
        )
        recast_df_authors(df)

        self.assertTrue(pd.isna(df.loc[0, "identifier"]))
        self.assertTrue(pd.isna(df.loc[0, "eid"]))
        self.assertTrue(pd.isna(df.loc[0, "first_name"]))


class AuthorkeywordsToScopusSearchTests(SimpleTestCase):
    def test_concatena_keywords_separadas_por_pipe(self):
        result = authorkeywords_to_scopus_search([{"$": "IA"}, {"$": "ML"}])
        self.assertEqual(result, "IA | ML")

    def test_ignora_items_sin_dollar_key(self):
        result = authorkeywords_to_scopus_search([{"other": "x"}])
        self.assertEqual(result, "")


class AffiliationToScopusSearchTests(SimpleTestCase):
    def test_reestructura_lista_de_afiliaciones(self):
        affils = [
            {
                "@href": "http://x",
                "@id": "60072059",
                "affilname": "ESPOL",
                "affiliation-city": "Guayaquil",
                "affiliation-country": "Ecuador",
            }
        ]
        result = affiliation_to_scopus_search(affils)
        self.assertEqual(result[0]["afid"], "60072059")
        self.assertEqual(result[0]["affilname"], "ESPOL")

    def test_campos_faltantes_asumen_nan(self):
        affils = [
            {"@href": "http://x", "@id": "1", "affiliation-country": "Ecuador"}
        ]
        result = affiliation_to_scopus_search(affils)
        self.assertTrue(np.isnan(result[0]["affilname"]))
        self.assertTrue(np.isnan(result[0]["affiliation-city"]))


class AuthorToScopusSearchTests(SimpleTestCase):
    def test_reestructura_autor_simple_valores_escalares(self):
        # Regresion: un bug previo dejaba authname/surname/given-name/initials
        # envueltos en tuplas de 1 elemento por una coma sobrante.
        authors = [
            {
                "author-url": "http://x",
                "@auid": "111",
                "ce:indexed-name": "Perez A.",
                "ce:surname": "Perez",
                "ce:given-name": "Ana",
                "ce:initials": "A.",
            }
        ]
        result = author_to_scopus_search(authors)
        self.assertEqual(result[0]["authname"], "Perez A.")
        self.assertEqual(result[0]["surname"], "Perez")
        self.assertEqual(result[0]["given-name"], "Ana")
        self.assertEqual(result[0]["initials"], "A.")
        self.assertEqual(result[0]["afid"], [])

    def test_afiliacion_unica_se_convierte_en_lista(self):
        authors = [
            {
                "author-url": "http://x",
                "@auid": "111",
                "affiliation": {"@id": "60072059"},
            }
        ]
        result = author_to_scopus_search(authors)
        self.assertEqual(result[0]["afid"], [{"@_fa": "true", "$": "60072059"}])

    def test_lista_de_afiliaciones_se_mapea_completa(self):
        authors = [
            {
                "author-url": "http://x",
                "@auid": "111",
                "affiliation": [{"@id": "1"}, {"@id": "2"}],
            }
        ]
        result = author_to_scopus_search(authors)
        self.assertEqual(
            result[0]["afid"],
            [{"@_fa": "true", "$": "1"}, {"@_fa": "true", "$": "2"}],
        )


class ArticleRetrievalToScopusSearchTests(SimpleTestCase):
    def test_extrae_identifier_afiliacion_y_autores(self):
        article_retrieval = {
            "coredata": {"dc:identifier": "SCOPUS_ID:1"},
            "affiliation": {"@href": "x", "@id": "1", "affiliation-country": "Ecuador"},
            "authors": {
                "author": [{"author-url": "x", "@auid": "1"}],
            },
        }
        result = article_retrieval_to_scopus_search(article_retrieval)
        self.assertEqual(result["dc:identifier"], "SCOPUS_ID:1")
        self.assertEqual(len(result["affiliation"]), 1)
        self.assertEqual(len(result["author"]), 1)

    def test_campos_ausentes_asumen_nan(self):
        result = article_retrieval_to_scopus_search({"coredata": {}})
        self.assertTrue(np.isnan(result["dc:identifier"]))
        self.assertTrue(np.isnan(result["affiliation"]))
        self.assertTrue(np.isnan(result["author"]))
