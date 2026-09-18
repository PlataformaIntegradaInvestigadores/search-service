"""Unitarias de: CorpusService (consultas Cypher contra Neo4j real de
pruebas), ModelGenerationService y ModelCorpusObserverService (mockeando
todo acceso a disco: nunca deben tocar los archivos reales de
resources/models o resources/corpus, que son de produccion)."""

from unittest.mock import MagicMock, mock_open, patch

from django.test import SimpleTestCase, TestCase
from neomodel import db

from apps.scopus_integration.application.services.corpus_generation_service import (
    CorpusService,
)
from apps.scopus_integration.application.services.model_corpus_observer_service import (
    ModelCorpusObserverService,
)
from apps.scopus_integration.application.services.model_generation_service import (
    ModelGenerationService,
)


class CorpusServiceTests(TestCase):
    def setUp(self):
        db.cypher_query("MATCH (n) WHERE n:Author OR n:Article OR n:Topic DETACH DELETE n")

    def tearDown(self):
        db.cypher_query("MATCH (n) WHERE n:Author OR n:Article OR n:Topic DETACH DELETE n")

    def test_get_corpus_by_author_agrupa_articulos_y_topicos(self):
        db.cypher_query(
            """
            CREATE (au:Author {scopus_id: "1"})
            CREATE (ar:Article {scopus_id: "10", title: "T", abstract: "A"})
            CREATE (to:Topic {name: "IA"})
            CREATE (au)-[:WROTE]->(ar)
            CREATE (ar)-[:USES]->(to)
            """
        )

        result = CorpusService().get_corpus_by_author()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["scopus_id"], "1")
        self.assertEqual(result[0]["articles"], [{"title": "T", "abstract": "A"}])
        self.assertEqual(result[0]["topics"], ["IA"])

    def test_get_corpus_by_author_sin_datos_retorna_lista_vacia(self):
        self.assertEqual(CorpusService().get_corpus_by_author(), [])

    def test_get_corpus_by_article_incluye_topicos_opcionales(self):
        db.cypher_query(
            'CREATE (:Article {scopus_id: "20", title: "T2", abstract: "A2"})'
        )

        result = CorpusService().get_corpus_by_article()

        self.assertEqual(result, [
            {"scopus_id": "20", "title": "T2", "abstract": "A2", "topics": []}
        ])

    def test_get_combined_corpus_combina_autores_y_articulos(self):
        db.cypher_query(
            """
            CREATE (au:Author {scopus_id: "1"})
            CREATE (ar:Article {scopus_id: "10", title: "T", abstract: "A"})
            CREATE (au)-[:WROTE]->(ar)
            """
        )

        combined = CorpusService().get_combined_corpus()

        doc_ids = {item["doc_id"] for item in combined}
        self.assertEqual(doc_ids, {"1", "10"})
        for item in combined:
            self.assertIn("doc", item)

    def test_get_corpus_by_author_error_neo4j_se_envuelve(self):
        with patch(
            "apps.scopus_integration.application.services."
            "corpus_generation_service.db"
        ) as mock_db:
            mock_db.cypher_query.side_effect = RuntimeError("boom")

            with self.assertRaises(Exception) as ctx:
                CorpusService().get_corpus_by_author()

            self.assertIn("Error while getting corpus by author", str(ctx.exception))


class ModelGenerationServiceTests(SimpleTestCase):
    def test_read_path_carga_pickle_desde_disco(self):
        with patch("builtins.open", mock_open(read_data=b"data")):
            with patch("pickle.load", return_value={"preprocessed_doc": []}) as mock_load:
                result = ModelGenerationService.read_path()

        mock_load.assert_called_once()
        self.assertEqual(result, {"preprocessed_doc": []})

    def test_read_path_error_se_envuelve(self):
        with patch("builtins.open", side_effect=FileNotFoundError("no existe")):
            with self.assertRaises(Exception) as ctx:
                ModelGenerationService.read_path()

        self.assertIn("Error reading path", str(ctx.exception))

    def test_save_model_escribe_pickle_sin_tocar_disco_real(self):
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("pickle.dump") as mock_dump:
                ModelGenerationService.save_model({"vocabulary": {}})

        mock_file.assert_called_once_with(
            "resources/models/tf-idf/model-v10.0.pkl", "wb"
        )
        mock_dump.assert_called_once()

    def test_save_model_error_se_envuelve(self):
        with patch("builtins.open", side_effect=OSError("disk full")):
            with self.assertRaises(Exception) as ctx:
                ModelGenerationService.save_model({})

        self.assertIn("Error saving model", str(ctx.exception))

    def test_generate_model_entrena_tfidf_y_guarda(self):
        import pandas as pd

        corpus = pd.DataFrame(
            {"preprocessed_doc": ["hola mundo", "mundo feliz"], "doc_id": ["1", "2"]}
        )
        service = ModelGenerationService()
        with patch.object(service, "save_model") as mock_save:
            service.generate_model(corpus)

        mock_save.assert_called_once()
        saved_model = mock_save.call_args.args[0]
        self.assertEqual(saved_model["indexes"], ["1", "2"])
        self.assertIn("vocabulary", saved_model)

    def test_generate_model_error_se_envuelve(self):
        service = ModelGenerationService()
        with self.assertRaises(Exception) as ctx:
            service.generate_model(None)

        self.assertIn("Error generating model", str(ctx.exception))


class ModelCorpusObserverServiceTests(SimpleTestCase):
    def test_construye_las_rutas_de_modelo_y_corpus(self):
        observer = ModelCorpusObserverService()
        self.assertEqual(observer.model_path, "resources/models/tf-idf/model-v10.0.pkl")
        self.assertEqual(observer.corpus_path, "resources/corpus/corpus-tf-idf-v10.0.pkl")

    def test_verify_model_path_exists_usa_os_path_exists_mockeado(self):
        observer = ModelCorpusObserverService()
        with patch("os.path.exists", return_value=True) as mock_exists:
            self.assertTrue(observer.verify_model_path_exists())
        mock_exists.assert_called_once_with(observer.model_path)

    def test_verify_corpus_path_exists_usa_os_path_exists_mockeado(self):
        observer = ModelCorpusObserverService()
        with patch("os.path.exists", return_value=False):
            self.assertFalse(observer.verify_corpus_path_exists())

    def test_delete_model_si_no_existe_retorna_true_sin_borrar(self):
        observer = ModelCorpusObserverService()
        with patch("os.path.exists", return_value=False):
            with patch("os.remove") as mock_remove:
                self.assertTrue(observer.delete_model())
        mock_remove.assert_not_called()

    def test_delete_model_si_existe_lo_borra_mockeado(self):
        observer = ModelCorpusObserverService()
        with patch("os.path.exists", return_value=True):
            with patch("os.remove") as mock_remove:
                self.assertTrue(observer.delete_model())
        mock_remove.assert_called_once_with(observer.model_path)

    def test_delete_corpus_si_existe_lo_borra_mockeado(self):
        observer = ModelCorpusObserverService()
        with patch("os.path.exists", return_value=True):
            with patch("os.remove") as mock_remove:
                self.assertTrue(observer.delete_corpus())
        mock_remove.assert_called_once_with(observer.corpus_path)

    def test_delete_model_error_se_envuelve(self):
        observer = ModelCorpusObserverService()
        with patch("os.path.exists", return_value=True):
            with patch("os.remove", side_effect=OSError("boom")):
                with self.assertRaises(Exception) as ctx:
                    observer.delete_model()
        self.assertIn("Error deleting model", str(ctx.exception))

    def test_delete_corpus_error_se_envuelve(self):
        observer = ModelCorpusObserverService()
        with patch("os.path.exists", return_value=True):
            with patch("os.remove", side_effect=OSError("boom")):
                with self.assertRaises(Exception) as ctx:
                    observer.delete_corpus()
        self.assertIn("Error deleting corpus", str(ctx.exception))
