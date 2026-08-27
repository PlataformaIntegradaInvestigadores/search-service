"""Unitarias del comando de management `upsert_mongo`: ETL incremental
Neo4j -> MongoDB. Mockea por completo neo4j.GraphDatabase, pymongo.MongoClient
y las funciones puras de apps.dashboards.utils.utils (pertenecen a otra app,
se tratan como colaboradores externos) para aislar la logica propia de este
comando: conexiones, orquestacion de _etl_*, construccion de operaciones
bulk_write y manejo de errores."""

from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import SimpleTestCase

from apps.scopus_integration.management.commands.upsert_mongo import Command

CMD = "apps.scopus_integration.management.commands.upsert_mongo"


def _year_entry(year, num):
    return {"year": year, "numArticles": num}


def _author_entry(sid, total, years, topics):
    return {"idScopus": sid, "totalArticles": total, "years": years, "topics": topics}


def _topic_entry(name, total, topic_years):
    return {"topic": name, "totalTopicArticles": total, "topic_years": topic_years}


class ConnectMongoTests(SimpleTestCase):
    def test_conexion_exitosa_retorna_cliente(self):
        cmd = Command()
        cmd.stdout = StringIO()
        with patch(f"{CMD}.MongoClient") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            result = cmd._connect_mongo()

        self.assertIs(result, mock_client)
        mock_client.admin.command.assert_called_once_with("ping")

    def test_conexion_fallida_retorna_none(self):
        cmd = Command()
        cmd.stdout = StringIO()
        with patch(f"{CMD}.MongoClient", side_effect=RuntimeError("no conecta")):
            result = cmd._connect_mongo()

        self.assertIsNone(result)


class ConnectNeo4jTests(SimpleTestCase):
    def test_conexion_exitosa_retorna_driver(self):
        cmd = Command()
        cmd.stdout = StringIO()
        with patch(f"{CMD}.GraphDatabase") as mock_graphdb:
            mock_driver = MagicMock()
            mock_graphdb.driver.return_value = mock_driver
            result = cmd._connect_neo4j()

        self.assertIs(result, mock_driver)
        mock_driver.verify_connectivity.assert_called_once()

    def test_conexion_fallida_retorna_none(self):
        cmd = Command()
        cmd.stdout = StringIO()
        with patch(f"{CMD}.GraphDatabase") as mock_graphdb:
            mock_graphdb.driver.side_effect = RuntimeError("no conecta")
            result = cmd._connect_neo4j()

        self.assertIsNone(result)


class EnsureIndexesTests(SimpleTestCase):
    def test_crea_indices_en_todas_las_colecciones(self):
        cmd = Command()
        cmd.stdout = StringIO()
        db = MagicMock()

        cmd._ensure_indexes(db)

        self.assertGreater(db.__getitem__.call_count, 0)

    def test_error_en_una_coleccion_no_detiene_las_demas(self):
        cmd = Command()
        cmd.stdout = StringIO()
        db = MagicMock()
        db.__getitem__.return_value.create_index.side_effect = RuntimeError("boom")

        cmd._ensure_indexes(db)  # no debe lanzar


class EtlAuthorsTests(SimpleTestCase):
    def test_sin_filas_retorna_lista_vacia(self):
        cmd = Command()
        cmd.stdout = StringIO()
        session = MagicMock()
        session.run.return_value.data.return_value = []

        result = cmd._etl_authors(session, MagicMock(), dry_run=False)

        self.assertEqual(result, [])

    def test_error_en_consulta_retorna_lista_vacia(self):
        cmd = Command()
        cmd.stdout = StringIO()
        session = MagicMock()
        session.run.side_effect = RuntimeError("boom")

        result = cmd._etl_authors(session, MagicMock(), dry_run=False)

        self.assertEqual(result, [])

    def test_filas_sin_fecha_de_publicacion_se_descartan(self):
        cmd = Command()
        cmd.stdout = StringIO()
        session = MagicMock()
        session.run.return_value.data.return_value = [
            {"au_id": "1", "ar_id": "10", "pub_date": None, "topic": None}
        ]
        db = MagicMock()

        with patch(f"{CMD}.extract_year", return_value=[]) as mock_extract, patch(
            f"{CMD}.count_articles_per_year_author", return_value=[]
        ) as mock_count:
            cmd._etl_authors(session, db, dry_run=False)

        mock_extract.assert_called_once_with([])
        mock_count.assert_called_once_with([], [], [], [])

    def test_construye_operaciones_bulk_write_y_persiste(self):
        cmd = Command()
        cmd.stdout = StringIO()
        session = MagicMock()
        session.run.return_value.data.return_value = [
            {"au_id": "1", "ar_id": "10", "pub_date": "2024-01-01", "topic": "IA"}
        ]
        db = MagicMock()
        db.__getitem__.return_value.bulk_write.return_value = MagicMock(
            upserted_count=1, modified_count=0
        )
        authors_data = [
            _author_entry(
                "1",
                3,
                [_year_entry(2023, 1), _year_entry(2024, 2)],
                [_topic_entry("IA", 3, [_year_entry(2023, 1), _year_entry(2024, 2)])],
            )
        ]

        with patch(f"{CMD}.extract_year", return_value=[2024]), patch(
            f"{CMD}.count_articles_per_year_author", return_value=authors_data
        ):
            result = cmd._etl_authors(session, db, dry_run=False)

        self.assertEqual(result, authors_data)
        self.assertTrue(db.__getitem__.return_value.bulk_write.called)

    def test_dry_run_no_escribe_en_mongo(self):
        cmd = Command()
        cmd.stdout = StringIO()
        session = MagicMock()
        session.run.return_value.data.return_value = [
            {"au_id": "1", "ar_id": "10", "pub_date": "2024-01-01", "topic": "IA"}
        ]
        db = MagicMock()
        authors_data = [_author_entry("1", 1, [_year_entry(2024, 1)], [])]

        with patch(f"{CMD}.extract_year", return_value=[2024]), patch(
            f"{CMD}.count_articles_per_year_author", return_value=authors_data
        ):
            cmd._etl_authors(session, db, dry_run=True)

        db.__getitem__.return_value.bulk_write.assert_not_called()


class EtlAffiliationsTests(SimpleTestCase):
    def test_construye_operaciones_y_persiste(self):
        cmd = Command()
        cmd.stdout = StringIO()
        session = MagicMock()
        session.run.return_value.data.return_value = [
            {
                "af_id": "60072059",
                "af_name": "ESPOL",
                "ar_id": "10",
                "pub_date": "2024-01-01",
                "topic": "IA",
            }
        ]
        db = MagicMock()
        db.__getitem__.return_value.bulk_write.return_value = MagicMock(
            upserted_count=1, modified_count=0
        )
        affiliations_data = [
            {
                "idScopus": "60072059",
                "name": "ESPOL",
                "totalArticles": 1,
                "years": [_year_entry(2024, 1)],
                "topics": [
                    _topic_entry("IA", 1, [_year_entry(2024, 1)]),
                ],
            }
        ]

        with patch(f"{CMD}.extract_year", return_value=[2024]), patch(
            f"{CMD}.count_articles_per_year_affiliation", return_value=affiliations_data
        ):
            result = cmd._etl_affiliations(session, db, dry_run=False)

        self.assertEqual(result, affiliations_data)
        self.assertTrue(db.__getitem__.return_value.bulk_write.called)

    def test_sin_filas_retorna_lista_vacia(self):
        cmd = Command()
        cmd.stdout = StringIO()
        session = MagicMock()
        session.run.return_value.data.return_value = []

        result = cmd._etl_affiliations(session, MagicMock(), dry_run=False)

        self.assertEqual(result, [])

    def test_error_en_consulta_retorna_lista_vacia(self):
        cmd = Command()
        cmd.stdout = StringIO()
        session = MagicMock()
        session.run.side_effect = RuntimeError("boom")

        result = cmd._etl_affiliations(session, MagicMock(), dry_run=False)

        self.assertEqual(result, [])


class EtlCountryTests(SimpleTestCase):
    def test_combina_articulos_autores_y_afiliaciones_por_anio(self):
        cmd = Command()
        cmd.stdout = StringIO()
        session = MagicMock()
        session.run.return_value.data.return_value = [
            {"ar_id": "10", "pub_date": "2024-01-01", "topic": "IA"}
        ]
        db = MagicMock()
        db.__getitem__.return_value.bulk_write.return_value = MagicMock(
            upserted_count=1, modified_count=0
        )

        country_raw = [
            {
                "years": [_year_entry(2024, 5)],
                "topics": [_topic_entry("IA", 5, [_year_entry(2024, 5)])],
                "totalArticles": 5,
            }
        ]
        articles_topics = {
            "Articles": {
                "Per_year": [{"name": "2024", "value": 5}],
                "Acumulative": [{"name": "2024", "value": 5}],
            },
            "Topics": {
                "Per_year": [{"name": "2024", "value": 1}],
                "Acumulative": [{"name": "2024", "value": 1}],
            },
        }
        authors_info = {
            "Per_year": [{"name": "2024", "value": 3}],
            "Acumulative": [{"name": "2024", "value": 3}],
        }
        affiliations_info = {
            "Per_year": [{"name": "2024", "value": 1}],
            "Acumulative": [{"name": "2024", "value": 1}],
        }

        with patch(f"{CMD}.extract_year", return_value=[2024]), patch(
            f"{CMD}.count_articles_per_year_country", return_value=country_raw
        ), patch(f"{CMD}.get_articles_topics_info", return_value=articles_topics), patch(
            f"{CMD}.get_authors_info", return_value=authors_info
        ), patch(
            f"{CMD}.get_affiliations_info", return_value=affiliations_info
        ):
            cmd._etl_country(session, db, dry_run=False, authors_data=[], affiliations_data=[])

        self.assertTrue(db.__getitem__.return_value.bulk_write.called)

    def test_error_en_consulta_retorna_sin_lanzar(self):
        cmd = Command()
        cmd.stdout = StringIO()
        session = MagicMock()
        session.run.side_effect = RuntimeError("boom")

        cmd._etl_country(session, MagicMock(), dry_run=False, authors_data=[], affiliations_data=[])


class EtlProvincesTests(SimpleTestCase):
    def test_construye_operaciones_y_persiste(self):
        cmd = Command()
        cmd.stdout = StringIO()
        session = MagicMock()
        session.run.return_value.data.return_value = [
            {
                "af_id": "1",
                "af_name": "x",
                "af_city": "Guayaquil",
                "ar_id": "10",
                "pub_date": "2024-01-01",
                "topic": "IA",
            }
        ]
        db = MagicMock()
        db.__getitem__.return_value.bulk_write.return_value = MagicMock(
            upserted_count=1, modified_count=0
        )
        provinces_data = [
            {
                "provincia": "Guayas",
                "num_articles": 1,
                "years": [_year_entry(2024, 1)],
                "topics": [_topic_entry("IA", 1, [_year_entry(2024, 1)])],
            }
        ]

        with patch(f"{CMD}.extract_year", return_value=[2024]), patch(
            f"{CMD}.process_affiliation_name", return_value="processed"
        ), patch(f"{CMD}.count_province", return_value=provinces_data):
            cmd._etl_provinces(session, db, dry_run=False)

        self.assertTrue(db.__getitem__.return_value.bulk_write.called)

    def test_filas_sin_ciudad_se_descartan(self):
        cmd = Command()
        cmd.stdout = StringIO()
        session = MagicMock()
        session.run.return_value.data.return_value = [
            {
                "af_id": "1",
                "af_name": "x",
                "af_city": None,
                "ar_id": "10",
                "pub_date": "2024-01-01",
                "topic": "IA",
            }
        ]
        db = MagicMock()

        with patch(f"{CMD}.extract_year", return_value=[]) as mock_extract, patch(
            f"{CMD}.process_affiliation_name", return_value="processed"
        ), patch(f"{CMD}.count_province", return_value=[]):
            cmd._etl_provinces(session, db, dry_run=False)

        mock_extract.assert_called_once_with([])

    def test_sin_filas_retorna_temprano(self):
        cmd = Command()
        cmd.stdout = StringIO()
        session = MagicMock()
        session.run.return_value.data.return_value = []

        cmd._etl_provinces(session, MagicMock(), dry_run=False)

    def test_error_en_consulta_retorna_sin_lanzar(self):
        cmd = Command()
        cmd.stdout = StringIO()
        session = MagicMock()
        session.run.side_effect = RuntimeError("boom")

        cmd._etl_provinces(session, MagicMock(), dry_run=False)


class BulkWriteAllTests(SimpleTestCase):
    def test_omite_colecciones_sin_operaciones(self):
        cmd = Command()
        cmd.stdout = StringIO()
        db = MagicMock()

        cmd._bulk_write_all(db, {"col": []}, dry_run=False)

        db.__getitem__.assert_not_called()

    def test_dry_run_no_ejecuta_bulk_write(self):
        cmd = Command()
        cmd.stdout = StringIO()
        db = MagicMock()

        cmd._bulk_write_all(db, {"col": [MagicMock()]}, dry_run=True)

        db.__getitem__.return_value.bulk_write.assert_not_called()

    def test_error_en_bulk_write_no_detiene_las_demas_colecciones(self):
        cmd = Command()
        cmd.stdout = StringIO()
        db = MagicMock()
        db.__getitem__.return_value.bulk_write.side_effect = RuntimeError("boom")

        cmd._bulk_write_all(db, {"col": [MagicMock()]}, dry_run=False)  # no debe lanzar


class HandleOrchestrationTests(SimpleTestCase):
    def test_mongo_no_disponible_retorna_temprano(self):
        with patch(f"{CMD}.Command._connect_mongo", return_value=None) as mock_mongo:
            call_command("upsert_mongo")

        mock_mongo.assert_called_once()

    def test_neo4j_no_disponible_cierra_mongo_y_retorna(self):
        mongo_client = MagicMock()
        with patch(f"{CMD}.Command._connect_mongo", return_value=mongo_client), patch(
            f"{CMD}.Command._connect_neo4j", return_value=None
        ):
            call_command("upsert_mongo")

        mongo_client.close.assert_called_once()

    def test_flujo_completo_llama_los_4_etl_y_cierra_conexiones(self):
        mongo_client = MagicMock()
        neo4j_driver = MagicMock()
        session_cm = MagicMock()
        neo4j_driver.session.return_value.__enter__.return_value = session_cm

        with patch(f"{CMD}.Command._connect_mongo", return_value=mongo_client), patch(
            f"{CMD}.Command._connect_neo4j", return_value=neo4j_driver
        ), patch(f"{CMD}.Command._ensure_indexes") as mock_indexes, patch(
            f"{CMD}.Command._etl_authors", return_value=[]
        ) as mock_authors, patch(
            f"{CMD}.Command._etl_affiliations", return_value=[]
        ) as mock_affils, patch(
            f"{CMD}.Command._etl_country"
        ) as mock_country, patch(
            f"{CMD}.Command._etl_provinces"
        ) as mock_provinces:
            call_command("upsert_mongo")

        mock_indexes.assert_called_once()
        mock_authors.assert_called_once()
        mock_affils.assert_called_once()
        mock_country.assert_called_once()
        mock_provinces.assert_called_once()
        neo4j_driver.close.assert_called_once()
        mongo_client.close.assert_called_once()

    def test_skip_indexes_omite_creacion_de_indices(self):
        mongo_client = MagicMock()
        neo4j_driver = MagicMock()
        neo4j_driver.session.return_value.__enter__.return_value = MagicMock()

        with patch(f"{CMD}.Command._connect_mongo", return_value=mongo_client), patch(
            f"{CMD}.Command._connect_neo4j", return_value=neo4j_driver
        ), patch(f"{CMD}.Command._ensure_indexes") as mock_indexes, patch(
            f"{CMD}.Command._etl_authors", return_value=[]
        ), patch(f"{CMD}.Command._etl_affiliations", return_value=[]), patch(
            f"{CMD}.Command._etl_country"
        ), patch(f"{CMD}.Command._etl_provinces"):
            call_command("upsert_mongo", "--skip-indexes")

        mock_indexes.assert_not_called()

    def test_dry_run_se_propaga_y_cierra_conexiones_pese_a_error_fatal(self):
        mongo_client = MagicMock()
        neo4j_driver = MagicMock()
        neo4j_driver.session.return_value.__enter__.return_value = MagicMock()

        with patch(f"{CMD}.Command._connect_mongo", return_value=mongo_client), patch(
            f"{CMD}.Command._connect_neo4j", return_value=neo4j_driver
        ), patch(f"{CMD}.Command._ensure_indexes"), patch(
            f"{CMD}.Command._etl_authors", side_effect=RuntimeError("boom")
        ):
            call_command("upsert_mongo", "--dry-run")

        neo4j_driver.close.assert_called_once()
        mongo_client.close.assert_called_once()
