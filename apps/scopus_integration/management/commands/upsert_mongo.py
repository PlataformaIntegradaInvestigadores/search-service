import os

from django.conf import settings
from django.core.management.base import BaseCommand
from neo4j import GraphDatabase
from pymongo import ASCENDING, MongoClient, UpdateOne

from apps.dashboards.utils.utils import (
    count_articles_per_year_affiliation,
    count_articles_per_year_author,
    count_articles_per_year_country,
    count_province,
    extract_year,
    get_affiliations_info,
    get_articles_topics_info,
    get_authors_info,
    process_affiliation_name,
)


class Command(BaseCommand):
    help = "ETL incremental: sincroniza Neo4j → MongoDB usando upsert masivo (sin borrar datos existentes)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula el ETL sin escribir en MongoDB",
        )
        parser.add_argument(
            "--skip-indexes",
            action="store_true",
            help="Omite la creación/verificación de índices",
        )

    # ------------------------------------------------------------------
    # Punto de entrada
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        skip_indexes = options["skip_indexes"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("MODO DRY-RUN activado. No se escribirá en MongoDB.")
            )

        self.stdout.write(self.style.WARNING("=== ETL INCREMENTAL INICIADO ==="))

        # ── Conexión MongoDB ──────────────────────────────────────────
        mongo_client = self._connect_mongo()
        if mongo_client is None:
            return
        db = mongo_client[
            os.environ.get(
                "MONGO_DB_NAME", getattr(settings, "MONGO_DB_NAME", "centinela")
            )
        ]

        # ── Conexión Neo4j ────────────────────────────────────────────
        neo4j_driver = self._connect_neo4j()
        if neo4j_driver is None:
            mongo_client.close()
            return

        try:
            if not skip_indexes:
                self._ensure_indexes(db)

            with neo4j_driver.session() as session:
                authors_data = self._etl_authors(session, db, dry_run)
                affiliations_data = self._etl_affiliations(session, db, dry_run)
                self._etl_country(session, db, dry_run, authors_data, affiliations_data)
                self._etl_provinces(session, db, dry_run)

        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Error fatal durante el ETL: {exc}"))
        finally:
            neo4j_driver.close()
            mongo_client.close()

        self.stdout.write(self.style.SUCCESS("=== ETL INCREMENTAL FINALIZADO ==="))

    # ------------------------------------------------------------------
    # Conexiones
    # ------------------------------------------------------------------

    def _connect_mongo(self):
        host = os.environ.get(
            "MONGO_DB_HOST", getattr(settings, "MONGO_DB_HOST", "localhost")
        )
        port = int(
            os.environ.get("MONGO_DB_PORT", getattr(settings, "MONGO_DB_PORT", 27017))
        )
        username = os.environ.get(
            "MONGO_DB_USERNAME", getattr(settings, "MONGO_DB_USERNAME", None)
        )
        password = os.environ.get(
            "MONGO_DB_PASSWORD", getattr(settings, "MONGO_DB_PASSWORD", None)
        )

        self.stdout.write(f"[MongoDB] Conectando → {host}:{port}")
        try:
            if username and password:
                client = MongoClient(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    authSource="admin",
                    serverSelectionTimeoutMS=5000,
                )
            else:
                client = MongoClient(
                    host=host, port=port, serverSelectionTimeoutMS=5000
                )
            client.admin.command("ping")
            self.stdout.write(self.style.SUCCESS("[MongoDB] Conexión establecida."))
            return client
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"[MongoDB] No se pudo conectar: {exc}"))
            return None

    def _connect_neo4j(self):
        host = os.environ.get("NEO4J_HOST", "localhost")
        port = os.environ.get("NEO4J_PORT", "7687")
        username = os.environ.get("NEO4J_USERNAME", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "")
        debug = os.environ.get("DEBUG", "True") == "True"
        scheme = "bolt" if debug else "bolt+s"
        uri = f"{scheme}://{host}:{port}"

        self.stdout.write(f"[Neo4j] Conectando → {uri}")
        try:
            driver = GraphDatabase.driver(uri, auth=(username, password))
            driver.verify_connectivity()
            self.stdout.write(self.style.SUCCESS("[Neo4j] Conexión establecida."))
            return driver
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"[Neo4j] No se pudo conectar: {exc}"))
            return None

    # ------------------------------------------------------------------
    # Índices (creados si no existen — operación idempotente)
    # ------------------------------------------------------------------

    def _ensure_indexes(self, db):
        self.stdout.write("[Índices] Verificando/creando índices...")
        specs = {
            "author": [("scopus_id", ASCENDING)],
            "author_year": [("scopus_id", ASCENDING), ("year", ASCENDING)],
            "author_acumulated": [("scopus_id", ASCENDING), ("year", ASCENDING)],
            "author_topics": [("scopus_id", ASCENDING), ("topic_name", ASCENDING)],
            "author_topics_year": [
                ("scopus_id", ASCENDING),
                ("topic_name", ASCENDING),
                ("year", ASCENDING),
            ],
            "author_topics_acumulated": [
                ("scopus_id", ASCENDING),
                ("topic_name", ASCENDING),
                ("year", ASCENDING),
            ],
            "affiliation": [("scopus_id", ASCENDING)],
            "affiliation_year": [("scopus_id", ASCENDING), ("year", ASCENDING)],
            "affiliation_acumulated": [("scopus_id", ASCENDING), ("year", ASCENDING)],
            "affiliation_topics": [("scopus_id", ASCENDING), ("topic_name", ASCENDING)],
            "affiliation_topics_year": [
                ("scopus_id", ASCENDING),
                ("topic_name", ASCENDING),
                ("year", ASCENDING),
            ],
            "affiliation_topics_acumulated": [
                ("scopus_id", ASCENDING),
                ("topic_name", ASCENDING),
                ("year", ASCENDING),
            ],
            "country_year": [("year", ASCENDING)],
            "country_acumulated": [("year", ASCENDING)],
            "country_topics": [("topic_name", ASCENDING)],
            "country_topics_year": [("topic_name", ASCENDING), ("year", ASCENDING)],
            "country_topics_acumulated": [
                ("topic_name", ASCENDING),
                ("year", ASCENDING),
            ],
            "province": [("province_name", ASCENDING)],
            "province_year": [("province_name", ASCENDING), ("year", ASCENDING)],
            "province_acumulated": [("province_name", ASCENDING), ("year", ASCENDING)],
            "province_topics_year": [
                ("province_name", ASCENDING),
                ("topic_name", ASCENDING),
                ("year", ASCENDING),
            ],
            "province_topics_acumulated": [
                ("province_name", ASCENDING),
                ("topic_name", ASCENDING),
                ("year", ASCENDING),
            ],
        }
        for col_name, keys in specs.items():
            try:
                db[col_name].create_index(keys, background=True)
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"[Índices] {col_name}: {exc}"))
        self.stdout.write(self.style.SUCCESS("[Índices] Listo."))

    # ------------------------------------------------------------------
    # ETL: Autores
    # ------------------------------------------------------------------

    def _etl_authors(self, session, db, dry_run):
        self.stdout.write("[Autores] Consultando Neo4j...")
        try:
            result = session.run("""
                MATCH (au:Author)-[:WROTE]->(ar:Article)
                OPTIONAL MATCH (ar)-[:USES]->(t:Topic)
                RETURN au.scopus_id AS au_id,
                       ar.scopus_id AS ar_id,
                       ar.publication_date AS pub_date,
                       t.name AS topic
            """)
            rows = result.data()
        except Exception as exc:
            self.stdout.write(
                self.style.ERROR(f"[Autores] Error en consulta Neo4j: {exc}")
            )
            return []

        if not rows:
            self.stdout.write("[Autores] Sin datos en Neo4j.")
            return []

        au_ids, ar_ids, pub_dates, topics = [], [], [], []
        for r in rows:
            if r["pub_date"] is None:
                continue
            au_ids.append(r["au_id"])
            ar_ids.append(r["ar_id"])
            pub_dates.append(r["pub_date"])
            topics.append(r["topic"])

        years = extract_year(pub_dates)
        authors_data = count_articles_per_year_author(au_ids, ar_ids, years, topics)
        self.stdout.write(f"[Autores] {len(authors_data)} autores procesados.")

        ops = {
            "author": [],
            "author_year": [],
            "author_acumulated": [],
            "author_topics": [],
            "author_topics_year": [],
            "author_topics_acumulated": [],
        }

        for author in authors_data:
            sid = author["idScopus"]
            total = author["totalArticles"]

            ops["author"].append(
                UpdateOne(
                    {"scopus_id": sid},
                    {"$set": {"scopus_id": sid, "total_articles": total}},
                    upsert=True,
                )
            )

            for y in author["years"]:
                yr = int(y["year"])
                ops["author_year"].append(
                    UpdateOne(
                        {"scopus_id": sid, "year": yr},
                        {"$set": {"total_articles": y["numArticles"]}},
                        upsert=True,
                    )
                )

            acum = 0
            for y in sorted(author["years"], key=lambda x: x["year"]):
                yr = int(y["year"])
                acum += y["numArticles"]
                ops["author_acumulated"].append(
                    UpdateOne(
                        {"scopus_id": sid, "year": yr},
                        {"$set": {"total_articles": acum}},
                        upsert=True,
                    )
                )

            topic_totals = {}
            for td in author["topics"]:
                tname = td["topic"]
                if tname is None:
                    continue
                topic_totals[tname] = td["totalTopicArticles"]

                acum_t = 0
                for y in sorted(td["topic_years"], key=lambda x: x["year"]):
                    yr = int(y["year"])
                    ops["author_topics_year"].append(
                        UpdateOne(
                            {"scopus_id": sid, "topic_name": tname, "year": yr},
                            {"$set": {"total_articles": y["numArticles"]}},
                            upsert=True,
                        )
                    )
                    acum_t += y["numArticles"]
                    ops["author_topics_acumulated"].append(
                        UpdateOne(
                            {"scopus_id": sid, "topic_name": tname, "year": yr},
                            {"$set": {"total_articles": acum_t}},
                            upsert=True,
                        )
                    )

            for tname, ttotal in topic_totals.items():
                ops["author_topics"].append(
                    UpdateOne(
                        {"scopus_id": sid, "topic_name": tname},
                        {"$set": {"total_articles": ttotal}},
                        upsert=True,
                    )
                )

        self._bulk_write_all(db, ops, dry_run, label="Autores")
        return authors_data

    # ------------------------------------------------------------------
    # ETL: Afiliaciones
    # ------------------------------------------------------------------

    def _etl_affiliations(self, session, db, dry_run):
        self.stdout.write("[Afiliaciones] Consultando Neo4j...")
        try:
            result = session.run("""
                MATCH (ar:Article)-[:BELONGS_TO]->(af:Affiliation)
                OPTIONAL MATCH (ar)-[:USES]->(t:Topic)
                RETURN af.scopus_id AS af_id,
                       af.name      AS af_name,
                       ar.scopus_id AS ar_id,
                       ar.publication_date AS pub_date,
                       t.name AS topic
            """)
            rows = result.data()
        except Exception as exc:
            self.stdout.write(
                self.style.ERROR(f"[Afiliaciones] Error en consulta Neo4j: {exc}")
            )
            return []

        if not rows:
            self.stdout.write("[Afiliaciones] Sin datos en Neo4j.")
            return []

        af_ids, af_names, ar_ids, pub_dates, topics = [], [], [], [], []
        for r in rows:
            if r["pub_date"] is None:
                continue
            af_ids.append(r["af_id"])
            af_names.append(r["af_name"])
            ar_ids.append(r["ar_id"])
            pub_dates.append(r["pub_date"])
            topics.append(r["topic"])

        years = extract_year(pub_dates)
        affiliations_data = count_articles_per_year_affiliation(
            af_ids, af_names, ar_ids, years, topics
        )
        self.stdout.write(
            f"[Afiliaciones] {len(affiliations_data)} afiliaciones procesadas."
        )

        ops = {
            "affiliation": [],
            "affiliation_year": [],
            "affiliation_acumulated": [],
            "affiliation_topics": [],
            "affiliation_topics_year": [],
            "affiliation_topics_acumulated": [],
        }

        for af in affiliations_data:
            sid = af["idScopus"]
            name = af["name"]
            total = af["totalArticles"]

            ops["affiliation"].append(
                UpdateOne(
                    {"scopus_id": sid},
                    {"$set": {"scopus_id": sid, "name": name, "total_articles": total}},
                    upsert=True,
                )
            )

            for y in af["years"]:
                yr = int(y["year"])
                total_topics_yr = len(
                    {
                        td["topic"]
                        for td in af["topics"]
                        if td["topic"] is not None
                        and any(int(ty["year"]) == yr for ty in td["topic_years"])
                    }
                )
                ops["affiliation_year"].append(
                    UpdateOne(
                        {"scopus_id": sid, "year": yr},
                        {
                            "$set": {
                                "name": name,
                                "total_articles": y["numArticles"],
                                "total_topics": total_topics_yr,
                            }
                        },
                        upsert=True,
                    )
                )

            acum_art = 0
            acum_topics = set()
            for y in sorted(af["years"], key=lambda x: x["year"]):
                yr = int(y["year"])
                acum_art += y["numArticles"]
                acum_topics.update(
                    {
                        td["topic"]
                        for td in af["topics"]
                        if td["topic"] is not None
                        and any(int(ty["year"]) == yr for ty in td["topic_years"])
                    }
                )
                ops["affiliation_acumulated"].append(
                    UpdateOne(
                        {"scopus_id": sid, "year": yr},
                        {
                            "$set": {
                                "name": name,
                                "total_articles": acum_art,
                                "total_topics": len(acum_topics),
                            }
                        },
                        upsert=True,
                    )
                )

            for td in af["topics"]:
                tname = td["topic"]
                if tname is None:
                    continue
                ops["affiliation_topics"].append(
                    UpdateOne(
                        {"scopus_id": sid, "topic_name": tname},
                        {
                            "$set": {
                                "name": name,
                                "total_articles": td["totalTopicArticles"],
                            }
                        },
                        upsert=True,
                    )
                )

                acum_t = 0
                for ty in sorted(td["topic_years"], key=lambda x: x["year"]):
                    yr = int(ty["year"])
                    acum_t += ty["numArticles"]
                    ops["affiliation_topics_year"].append(
                        UpdateOne(
                            {"scopus_id": sid, "topic_name": tname, "year": yr},
                            {
                                "$set": {
                                    "name": name,
                                    "total_articles": ty["numArticles"],
                                }
                            },
                            upsert=True,
                        )
                    )
                    ops["affiliation_topics_acumulated"].append(
                        UpdateOne(
                            {"scopus_id": sid, "topic_name": tname, "year": yr},
                            {"$set": {"name": name, "total_articles": acum_t}},
                            upsert=True,
                        )
                    )

        self._bulk_write_all(db, ops, dry_run, label="Afiliaciones")
        return affiliations_data

    # ------------------------------------------------------------------
    # ETL: País (Ecuador)
    # ------------------------------------------------------------------

    def _etl_country(self, session, db, dry_run, authors_data, affiliations_data):
        self.stdout.write("[País] Consultando Neo4j...")
        try:
            art_result = session.run("""
                MATCH (ar:Article)
                OPTIONAL MATCH (ar)-[:USES]->(t:Topic)
                RETURN ar.scopus_id AS ar_id,
                       ar.publication_date AS pub_date,
                       t.name AS topic
            """)
            art_rows = art_result.data()
        except Exception as exc:
            self.stdout.write(
                self.style.ERROR(f"[País] Error en consulta Neo4j: {exc}")
            )
            return

        # ── Artículos / tópicos por año ───────────────────────────────
        ar_ids, pub_dates, topics = [], [], []
        for r in art_rows:
            if r["pub_date"] is None:
                continue
            ar_ids.append(r["ar_id"])
            pub_dates.append(r["pub_date"])
            topics.append(r["topic"])

        years = extract_year(pub_dates)
        country_raw = count_articles_per_year_country(ar_ids, years, topics)
        countries = [
            {
                "name": "Ecuador",
                "years": [
                    {"year": y["year"], "num_articles": y["numArticles"]}
                    for y in c["years"]
                ],
                "topics": [
                    {
                        "topic_name": t["topic"],
                        "num_articles_per_year": [
                            {"year": ty["year"], "num_articles": ty["numArticles"]}
                            for ty in t["topic_years"]
                        ],
                        "total_topic_articles": t["totalTopicArticles"],
                    }
                    for t in c["topics"]
                    if t["topic"] is not None
                ],
                "total_articles": c["totalArticles"],
            }
            for c in country_raw
        ]

        articles_topics = get_articles_topics_info(countries)

        # ── Autores por año (reusa lo ya calculado en _etl_authors — misma
        #    consulta Cypher, evita un segundo escaneo completo del grafo) ──
        authors_list = [
            {
                "scopus_id": a["idScopus"],
                "years": [
                    {"year": y["year"], "num_articles": y["numArticles"]}
                    for y in a["years"]
                ],
                "total_articles": a["totalArticles"],
            }
            for a in authors_data
        ]
        authors_info = get_authors_info(authors_list)

        # ── Afiliaciones por año (reusa lo ya calculado en _etl_affiliations) ──
        aff_list = [
            {
                "id_affiliation": a["idScopus"],
                "years": [
                    {"year": y["year"], "num_articles": y["numArticles"]}
                    for y in a["years"]
                ],
            }
            for a in affiliations_data
        ]
        affiliations_info = get_affiliations_info(aff_list)

        ops = {
            "country_year": [],
            "country_acumulated": [],
            "country_topics": [],
            "country_topics_year": [],
            "country_topics_acumulated": [],
        }

        for yd in articles_topics["Articles"]["Per_year"]:
            yr = int(yd["name"])
            total_auth = next(
                (
                    int(x["value"])
                    for x in authors_info["Per_year"]
                    if int(x["name"]) == yr
                ),
                0,
            )
            total_aff = next(
                (
                    int(x["value"])
                    for x in affiliations_info["Per_year"]
                    if int(x["name"]) == yr
                ),
                0,
            )
            total_top = next(
                (
                    int(x["value"])
                    for x in articles_topics["Topics"]["Per_year"]
                    if int(x["name"]) == yr
                ),
                0,
            )
            ops["country_year"].append(
                UpdateOne(
                    {"year": yr},
                    {
                        "$set": {
                            "total_articles": int(yd["value"]),
                            "total_authors": total_auth,
                            "total_affiliations": total_aff,
                            "total_topics": total_top,
                        }
                    },
                    upsert=True,
                )
            )

        for yd in articles_topics["Articles"]["Acumulative"]:
            yr = int(yd["name"])
            total_auth = next(
                (
                    int(x["value"])
                    for x in authors_info["Acumulative"]
                    if int(x["name"]) == yr
                ),
                0,
            )
            total_aff = next(
                (
                    int(x["value"])
                    for x in affiliations_info["Acumulative"]
                    if int(x["name"]) == yr
                ),
                0,
            )
            total_top = next(
                (
                    int(x["value"])
                    for x in articles_topics["Topics"]["Acumulative"]
                    if int(x["name"]) == yr
                ),
                0,
            )
            ops["country_acumulated"].append(
                UpdateOne(
                    {"year": yr},
                    {
                        "$set": {
                            "total_articles": int(yd["value"]),
                            "total_authors": total_auth,
                            "total_affiliations": total_aff,
                            "total_topics": total_top,
                        }
                    },
                    upsert=True,
                )
            )

        for country in countries:
            for td in country["topics"]:
                tname = td["topic_name"]
                ops["country_topics"].append(
                    UpdateOne(
                        {"topic_name": tname},
                        {"$set": {"total_articles": td["total_topic_articles"]}},
                        upsert=True,
                    )
                )
                acum_t = 0
                for yd in sorted(td["num_articles_per_year"], key=lambda x: x["year"]):
                    yr = int(yd["year"])
                    ops["country_topics_year"].append(
                        UpdateOne(
                            {"topic_name": tname, "year": yr},
                            {"$set": {"total_articles": yd["num_articles"]}},
                            upsert=True,
                        )
                    )
                    acum_t += yd["num_articles"]
                    ops["country_topics_acumulated"].append(
                        UpdateOne(
                            {"topic_name": tname, "year": yr},
                            {"$set": {"total_articles": acum_t}},
                            upsert=True,
                        )
                    )

        self.stdout.write("[País] Datos de Ecuador procesados.")
        self._bulk_write_all(db, ops, dry_run, label="País")

    # ------------------------------------------------------------------
    # ETL: Provincias
    # ------------------------------------------------------------------

    def _etl_provinces(self, session, db, dry_run):
        self.stdout.write("[Provincias] Consultando Neo4j...")
        try:
            result = session.run("""
                MATCH (ar:Article)-[:BELONGS_TO]->(af:Affiliation)
                OPTIONAL MATCH (ar)-[:USES]->(t:Topic)
                RETURN af.scopus_id AS af_id,
                       af.name      AS af_name,
                       af.city      AS af_city,
                       ar.scopus_id AS ar_id,
                       ar.publication_date AS pub_date,
                       t.name AS topic
            """)
            rows = result.data()
        except Exception as exc:
            self.stdout.write(
                self.style.ERROR(f"[Provincias] Error en consulta Neo4j: {exc}")
            )
            return

        if not rows:
            self.stdout.write("[Provincias] Sin datos en Neo4j.")
            return

        af_cities, ar_ids, pub_dates, topics = [], [], [], []
        for r in rows:
            if r["pub_date"] is None or r["af_city"] is None:
                continue
            af_cities.append(r["af_city"])
            ar_ids.append(r["ar_id"])
            pub_dates.append(r["pub_date"])
            topics.append(r["topic"])

        years = extract_year(pub_dates)
        processed = process_affiliation_name(af_cities, ar_ids, years, topics)
        provinces_data = count_province(processed)
        self.stdout.write(f"[Provincias] {len(provinces_data)} provincias procesadas.")

        ops = {
            "province": [],
            "province_year": [],
            "province_acumulated": [],
            "province_topics_year": [],
            "province_topics_acumulated": [],
        }

        for prov in provinces_data:
            pname = prov["provincia"]
            total = prov["num_articles"]

            ops["province"].append(
                UpdateOne(
                    {"province_name": pname},
                    {"$set": {"total_articles": total}},
                    upsert=True,
                )
            )

            for y in prov["years"]:
                yr = int(y["year"])
                ops["province_year"].append(
                    UpdateOne(
                        {"province_name": pname, "year": yr},
                        {"$set": {"total_articles": y["numArticles"]}},
                        upsert=True,
                    )
                )

            acum = 0
            for y in sorted(prov["years"], key=lambda x: x["year"]):
                yr = int(y["year"])
                acum += y["numArticles"]
                ops["province_acumulated"].append(
                    UpdateOne(
                        {"province_name": pname, "year": yr},
                        {"$set": {"total_articles": acum}},
                        upsert=True,
                    )
                )

            for td in prov["topics"]:
                tname = td["topic"]
                if tname is None:
                    continue
                acum_t = 0
                for ty in sorted(td["topic_years"], key=lambda x: x["year"]):
                    yr = int(ty["year"])
                    ops["province_topics_year"].append(
                        UpdateOne(
                            {"province_name": pname, "topic_name": tname, "year": yr},
                            {"$set": {"total_articles": ty["numArticles"]}},
                            upsert=True,
                        )
                    )
                    acum_t += ty["numArticles"]
                    ops["province_topics_acumulated"].append(
                        UpdateOne(
                            {"province_name": pname, "topic_name": tname, "year": yr},
                            {"$set": {"total_articles": acum_t}},
                            upsert=True,
                        )
                    )

        self._bulk_write_all(db, ops, dry_run, label="Provincias")

    # ------------------------------------------------------------------
    # Utilidad: ejecutar bulk_write en múltiples colecciones
    # ------------------------------------------------------------------

    def _bulk_write_all(self, db, ops_map, dry_run, label=""):
        for col_name, ops in ops_map.items():
            if not ops:
                continue
            if dry_run:
                self.stdout.write(
                    f"  [DRY-RUN] {label} / {col_name}: {len(ops)} operaciones pendientes."
                )
                continue
            try:
                result = db[col_name].bulk_write(ops, ordered=False)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  [{label}] {col_name}: "
                        f"insertados={result.upserted_count}, "
                        f"actualizados={result.modified_count}"
                    )
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"  [{label}] {col_name}: Error en bulk_write → {exc}"
                    )
                )
