from django.db import transaction
from neomodel import db

from apps.dashboards.domain.entities.affiliation import Affiliation
from apps.dashboards.domain.entities.affiliation_topics import AffiliationTopics
from apps.dashboards.domain.entities.affiliation_topics_acumulated import (
    AffiliationTopicsAcumulated,
)
from apps.dashboards.domain.entities.affiliation_topics_year import (
    AffiliationTopicsYear,
)
from apps.dashboards.domain.entities.affiliation_year import AffiliationYear
from apps.dashboards.domain.entities.affiliation_year_acumulated import (
    AffiliationAcumulated,
)
from apps.dashboards.domain.entities.author import Author
from apps.dashboards.domain.entities.author_topics import AuthorTopics
from apps.dashboards.domain.entities.author_topics_acumulated import (
    AuthorTopicsAcumulated,
)
from apps.dashboards.domain.entities.author_topics_year import AuthorTopicsYear
from apps.dashboards.domain.entities.author_year import AuthorYear
from apps.dashboards.domain.entities.author_year_acumulated import AuthorAcumulated
from apps.dashboards.domain.entities.country_acumulated import CountryAcumulated
from apps.dashboards.domain.entities.country_topics import CountryTopics
from apps.dashboards.domain.entities.country_topics_acumulated import (
    CountryTopicsAcumulated,
)
from apps.dashboards.domain.entities.country_topics_year import CountryTopicsYear
from apps.dashboards.domain.entities.country_year import CountryYear
from apps.dashboards.domain.entities.province import Province
from apps.dashboards.domain.entities.province_acumulated import ProvinceAcumulated
from apps.dashboards.domain.entities.province_topics_acumulated import (
    ProvinceTopicsAcumulated,
)
from apps.dashboards.domain.entities.province_topics_year import ProvinceTopicsYear
from apps.dashboards.domain.entities.province_year import ProvinceYear
from apps.dashboards.domain.repositories.populate_repository import PopulateRepository
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


class PopulateService(PopulateRepository):
    def populate(self):
        self.drop_database()
        self.populate_country()
        self.populate_affiliation()
        self.populate_province()
        self.populate_author()

    DASHBOARD_COLLECTIONS = [
        Affiliation,
        AffiliationTopics,
        AffiliationTopicsAcumulated,
        AffiliationTopicsYear,
        AffiliationYear,
        AffiliationAcumulated,
        Author,
        AuthorTopics,
        AuthorTopicsAcumulated,
        AuthorTopicsYear,
        AuthorYear,
        AuthorAcumulated,
        CountryAcumulated,
        CountryTopics,
        CountryTopicsAcumulated,
        CountryTopicsYear,
        CountryYear,
        Province,
        ProvinceAcumulated,
        ProvinceTopicsAcumulated,
        ProvinceTopicsYear,
        ProvinceYear,
    ]

    def drop_database(self):
        # dropDatabase requiere un rol de admin que el usuario de la app no
        # siempre tiene; dropear cada coleccion si requiere solo permiso de
        # escritura sobre esa coleccion y evita dejar datos duplicados de
        # una corrida anterior si el drop de la base fallaba en silencio.
        for collection in self.DASHBOARD_COLLECTIONS:
            try:
                collection.drop_collection()
            except Exception as e:
                print(f"Error dropping collection {collection.__name__}: {e}")

    def get_provinces_dict(self):
        query = """
            MATCH (ar:Article)-[b:BELONGS_TO]->(af:Affiliation)
            OPTIONAL MATCH (ar)-[u:USES]->(t:Topic)
            RETURN af.scopus_id, af.name, af.city, ar.scopus_id, ar.publication_date, t.name
        """
        results, meta = db.cypher_query(query)

        af_scopus_ids = []
        af_names = []
        af_cities = []
        ar_scopus_ids = []
        ar_publication_dates = []
        topics = []

        for result in results:
            af_scopus_ids.append(result[0])
            af_names.append(result[1])
            af_cities.append(result[2])
            ar_scopus_ids.append(result[3])
            ar_publication_dates.append(result[4])
            topics.append(result[5] if result[5] is not None else " ")

        years = extract_year(ar_publication_dates)
        provinces = process_affiliation_name(af_cities, ar_scopus_ids, years, topics)
        provinces_data = count_province(provinces)

        provinces_list = []

        for province_data in provinces_data:
            years = [
                {"year": year_info["year"], "num_articles": year_info["numArticles"]}
                for year_info in province_data["years"]
            ]

            topics_list = []
            for topic_data in province_data["topics"]:
                num_articles_per_year = [
                    {
                        "year": year_info["year"],
                        "num_articles": year_info["numArticles"],
                    }
                    for year_info in topic_data["topic_years"]
                ]
                topic = {
                    "topic_name": topic_data["topic"],
                    "num_articles_per_year": num_articles_per_year,
                    "total_topic_articles": topic_data["totalTopicArticles"],
                }
                topics_list.append(topic)

            province_dict = {
                "id_province": province_data["id_provincia"],
                "province_name": province_data["provincia"],
                "years": years,
                "topics": topics_list,
                "total_articles": province_data["num_articles"],
            }

            provinces_list.append(province_dict)

        return provinces_list

    def populate_province(self):
        provinces_list = self.get_provinces_dict()
        for province_data in provinces_list:
            province_name = province_data["province_name"]
            total_articles = province_data["total_articles"]

            # Mapear Province
            province = Province(
                province_name=province_name, total_articles=total_articles
            )
            province.save()

            # Mapear ProvinceYear
            for year_data in province_data["years"]:
                province_year = ProvinceYear(
                    province_name=province_name,
                    year=year_data["year"],
                    total_articles=year_data["num_articles"],
                )
                province_year.save()

            # Mapear ProvinceAcumulated
            acumulated_articles = 0
            for year_data in sorted(province_data["years"], key=lambda x: x["year"]):
                acumulated_articles += year_data["num_articles"]
                province_acumulated = ProvinceAcumulated(
                    province_name=province_name,
                    year=year_data["year"],
                    total_articles=acumulated_articles,
                )
                province_acumulated.save()

            for topic_data in province_data["topics"]:
                topic_name = topic_data["topic_name"]
                counted_topics = set()

                for year_data in topic_data["num_articles_per_year"]:
                    year = year_data["year"]

                    province_topics_year = ProvinceTopicsYear(
                        province_name=province_name,
                        topic_name=topic_name,
                        year=year,
                        total_articles=year_data["num_articles"],
                    )
                    province_topics_year.save()

                    if topic_name not in counted_topics:
                        counted_topics.add(topic_name)
                        province_topics_acumulated = ProvinceTopicsAcumulated(
                            province_name=province_name,
                            topic_name=topic_name,
                            year=year,
                            total_articles=year_data["num_articles"],
                        )
                        province_topics_acumulated.save()
                    else:
                        previous_acumulated = (
                            ProvinceTopicsAcumulated.objects.filter(
                                province_name=province_name,
                                topic_name=topic_name,
                                year__lt=year,
                            )
                            .order_by("-year")
                            .first()
                        )
                        if previous_acumulated:
                            new_total = previous_acumulated.total_articles
                        else:
                            new_total = 0

                        province_topics_acumulated = ProvinceTopicsAcumulated(
                            province_name=province_name,
                            topic_name=topic_name,
                            year=year,
                            total_articles=new_total,
                        )
                        province_topics_acumulated.save()

    def get_authors_dict(self):
        query = """
                    MATCH (au:Author)-[w:WROTE]->(ar:Article)
                    OPTIONAL MATCH (ar)-[u:USES]->(t:Topic)
                    RETURN au.scopus_id, ar.scopus_id, ar.publication_date, t.name
                    """
        results, meta = db.cypher_query(query)

        au_scopus_ids = []
        ar_scopus_ids = []
        ar_publication_dates = []
        topics = []

        for result in results:
            au_scopus_ids.append(result[0])
            ar_scopus_ids.append(result[1])
            ar_publication_dates.append(result[2])
            topics.append(result[3] if result[3] is not None else " ")

        years = extract_year(ar_publication_dates)

        authors_data = count_articles_per_year_author(
            au_scopus_ids, ar_scopus_ids, years, topics
        )

        authors_list = []

        for author_data in authors_data:
            # Crear diccionarios para YearContribution
            years = [
                {"year": year_info["year"], "num_articles": year_info["numArticles"]}
                for year_info in author_data["years"]
            ]

            # Crear diccionarios para Topic
            topics = []
            for topic_data in author_data["topics"]:
                num_articles_per_year = [
                    {
                        "year": year_info["year"],
                        "num_articles": year_info["numArticles"],
                    }
                    for year_info in topic_data["topic_years"]
                ]
                topic = {
                    "topic_name": topic_data["topic"],
                    "num_articles_per_year": num_articles_per_year,
                    "total_topic_articles": topic_data["totalTopicArticles"],
                }
                topics.append(topic)

            # Crear diccionario para Author
            author_dict = {
                "scopus_id": author_data["idScopus"],
                "years": years,
                "topics": topics,
                "total_articles": author_data["totalArticles"],
            }

            authors_list.append(author_dict)

        return authors_list

    @transaction.atomic
    def populate_author(self):
        authors_list = self.get_authors_dict()
        for author_data in authors_list:
            scopus_id = author_data["scopus_id"]
            total_articles = author_data["total_articles"]

            # Mapear Author
            author = Author(scopus_id=scopus_id, total_articles=total_articles)
            author.save()

            # Mapear AuthorYear
            for year_data in author_data["years"]:
                author_year = AuthorYear(
                    scopus_id=scopus_id,
                    year=year_data["year"],
                    total_articles=year_data["num_articles"],
                )
                author_year.save()

            # Mapear AuthorAcumulated
            acumulated_articles = 0
            for year_data in sorted(author_data["years"], key=lambda x: x["year"]):
                acumulated_articles += year_data["num_articles"]
                author_acumulated = AuthorAcumulated(
                    scopus_id=scopus_id,
                    year=year_data["year"],
                    total_articles=acumulated_articles,
                )
                author_acumulated.save()

            # Mapear AuthorTopicsYear y AuthorTopicsAcumulated
            topic_totals = {}
            for topic_data in author_data["topics"]:
                topic_name = topic_data["topic_name"]
                counted_topics = set()

                for year_data in topic_data["num_articles_per_year"]:
                    year = year_data["year"]

                    # AuthorTopicsYear
                    author_topics_year = AuthorTopicsYear(
                        scopus_id=scopus_id,
                        topic_name=topic_name,
                        year=year,
                        total_articles=year_data["num_articles"],
                    )
                    author_topics_year.save()

                    # Acumular el total de artículos por tópico
                    if topic_name in topic_totals:
                        topic_totals[topic_name] += year_data["num_articles"]
                    else:
                        topic_totals[topic_name] = year_data["num_articles"]

                    # AuthorTopicsAcumulated
                    if topic_name not in counted_topics:
                        counted_topics.add(topic_name)
                        author_topics_acumulated = AuthorTopicsAcumulated(
                            scopus_id=scopus_id,
                            topic_name=topic_name,
                            year=year,
                            total_articles=year_data["num_articles"],
                        )
                        author_topics_acumulated.save()
                    else:
                        previous_acumulated = (
                            AuthorTopicsAcumulated.objects.filter(
                                scopus_id=scopus_id,
                                topic_name=topic_name,
                                year__lt=year,
                            )
                            .order_by("-year")
                            .first()
                        )
                        if previous_acumulated:
                            new_total = previous_acumulated.total_articles
                        else:
                            new_total = 0

                        author_topics_acumulated = AuthorTopicsAcumulated(
                            scopus_id=scopus_id,
                            topic_name=topic_name,
                            year=year,
                            total_articles=new_total,
                        )
                        author_topics_acumulated.save()

            # Mapear AuthorTopics
            for topic_name, total_articles in topic_totals.items():
                author_topic = AuthorTopics(
                    scopus_id=scopus_id,
                    topic_name=topic_name,
                    total_articles=total_articles,
                )
                author_topic.save()

    def get_country_articles_topics_dict(self):
        query = """
                MATCH (ar:Article)
                OPTIONAL MATCH (ar)-[u:USES]->(t:Topic)
                RETURN ar.scopus_id, ar.publication_date, t.name
                """
        results, meta = db.cypher_query(query)

        ar_scopus_ids = []
        ar_publication_dates = []
        topics = []

        for result in results:
            ar_scopus_ids.append(result[0])
            ar_publication_dates.append(result[1])
            topics.append(result[2] if result[2] is not None else " ")

        years = extract_year(ar_publication_dates)

        country_data_list = count_articles_per_year_country(
            ar_scopus_ids, years, topics
        )

        country_dicts = []  # Utilizar una lista para almacenar los diccionarios de país

        for country_data in country_data_list:
            years_contributions = [
                {"year": year_info["year"], "num_articles": year_info["numArticles"]}
                for year_info in country_data["years"]
            ]

            topics_list = []
            for topic_data in country_data["topics"]:
                num_articles_per_year = [
                    {
                        "year": year_info["year"],
                        "num_articles": year_info["numArticles"],
                    }
                    for year_info in topic_data["topic_years"]
                ]
                topic = {
                    "topic_name": topic_data["topic"],
                    "num_articles_per_year": num_articles_per_year,
                    "total_topic_articles": topic_data["totalTopicArticles"],
                }
                topics_list.append(topic)

            country_dict = {
                "name": "Ecuador",
                "years": years_contributions,
                "topics": topics_list,
                "total_articles": country_data["totalArticles"],
            }

            country_dicts.append(country_dict)  # Agregar el diccionario a la lista

        return country_dicts

    def get_country_authors_dict(self):
        query = """
                MATCH (au:Author)-[w:WROTE]->(ar:Article)
                OPTIONAL MATCH (ar)-[u:USES]->(t:Topic)
                RETURN au.scopus_id, ar.scopus_id, ar.publication_date, t.name
                """
        results, meta = db.cypher_query(query)

        au_scopus_ids = []
        ar_scopus_ids = []
        ar_publication_dates = []
        topics = []

        for result in results:
            au_scopus_ids.append(result[0])
            ar_scopus_ids.append(result[1])
            ar_publication_dates.append(result[2])
            topics.append(result[3] if result[3] is not None else " ")

        years = extract_year(ar_publication_dates)

        authors_data = count_articles_per_year_author(
            au_scopus_ids, ar_scopus_ids, years, topics
        )

        authors_list = []

        for author_data in authors_data:
            years = [
                {"year": year_info["year"], "num_articles": year_info["numArticles"]}
                for year_info in author_data["years"]
            ]

            topics = []
            for topic_data in author_data["topics"]:
                num_articles_per_year = [
                    {
                        "year": year_info["year"],
                        "num_articles": year_info["numArticles"],
                    }
                    for year_info in topic_data["topic_years"]
                ]
                topic = {
                    "topic_name": topic_data["topic"],
                    "num_articles_per_year": num_articles_per_year,
                    "total_topic_articles": topic_data["totalTopicArticles"],
                }
                topics.append(topic)

            author_dict = {
                "scopus_id": author_data["idScopus"],
                "years": years,
                "topics": topics,
                "total_articles": author_data["totalArticles"],
            }

            authors_list.append(author_dict)
        authors = get_authors_info(authors_list)
        return authors

    def get_country_affiliations_dict(self):
        query = """
                MATCH (ar:Article)-[b:BELONGS_TO]->(af:Affiliation)
                OPTIONAL MATCH (ar)-[u:USES]->(t:Topic)
                RETURN af.scopus_id, af.name, ar.scopus_id, ar.publication_date, t.name
            """
        results, meta = db.cypher_query(query)

        af_scopus_ids = []
        af_names = []
        ar_scopus_ids = []
        ar_publication_dates = []
        topics = []

        for result in results:
            af_scopus_ids.append(result[0])
            af_names.append(result[1])
            ar_scopus_ids.append(result[2])
            ar_publication_dates.append(result[3])
            topics.append(result[4] if result[4] is not None else " ")

        years = extract_year(ar_publication_dates)

        affiliations_data = count_articles_per_year_affiliation(
            af_scopus_ids, af_names, ar_scopus_ids, years, topics
        )

        affiliations_list = []

        for affiliation_data in affiliations_data:
            # Crear diccionarios para YearContribution
            years = [
                {"year": year_info["year"], "num_articles": year_info["numArticles"]}
                for year_info in affiliation_data["years"]
            ]

            # Crear diccionarios para Topic
            topics = []
            for topic_data in affiliation_data["topics"]:
                num_articles_per_year = [
                    {
                        "year": year_info["year"],
                        "num_articles": year_info["numArticles"],
                    }
                    for year_info in topic_data["topic_years"]
                ]
                topic = {
                    "topic_name": topic_data["topic"],
                    "num_articles_per_year": num_articles_per_year,
                    "total_topic_articles": topic_data["totalTopicArticles"],
                }
                topics.append(topic)

            # Crear diccionario para Affiliation
            affiliation_dict = {
                "id_affiliation": affiliation_data["idScopus"],
                "name": affiliation_data["name"],  # Asegurarse de incluir el nombre
                "years": years,
                "topics": topics,
                "total_articles": affiliation_data["totalArticles"],
            }

            affiliations_list.append(affiliation_dict)

        affiliations = get_affiliations_info(affiliations_list)
        return affiliations

    @transaction.atomic
    def populate_country(self):
        authors = self.get_country_authors_dict()
        countries = self.get_country_articles_topics_dict()
        articles_topics = get_articles_topics_info(countries)
        affiliations = self.get_country_affiliations_dict()
        for year_data in articles_topics["Articles"]["Per_year"]:
            year = int(year_data["name"])
            total_authors = next(
                (
                    item["value"]
                    for item in authors["Per_year"]
                    if int(item["name"]) == year
                ),
                0,
            )
            total_affiliations = next(
                (
                    item["value"]
                    for item in affiliations["Per_year"]
                    if int(item["name"]) == year
                ),
                0,
            )
            total_topics = next(
                (
                    item["value"]
                    for item in articles_topics["Topics"]["Per_year"]
                    if int(item["name"]) == year
                ),
                0,
            )

            country_year = CountryYear(
                year=year,
                total_authors=total_authors,
                total_articles=year_data["value"],
                total_affiliations=total_affiliations,
                total_topics=total_topics,
            )
            country_year.save()

            # Mapeo para CountryAcumulated
        for year_data in articles_topics["Articles"]["Acumulative"]:
            year = int(year_data["name"])
            total_authors = next(
                (
                    item["value"]
                    for item in authors["Acumulative"]
                    if int(item["name"]) == year
                ),
                0,
            )
            total_affiliations = next(
                (
                    item["value"]
                    for item in affiliations["Acumulative"]
                    if int(item["name"]) == year
                ),
                0,
            )
            total_topics = next(
                (
                    item["value"]
                    for item in articles_topics["Topics"]["Acumulative"]
                    if int(item["name"]) == year
                ),
                0,
            )

            country_acumulated = CountryAcumulated(
                year=year,
                total_authors=total_authors,
                total_articles=year_data["value"],
                total_affiliations=total_affiliations,
                total_topics=total_topics,
            )
            country_acumulated.save()

        for country_data in countries:
            for topic_data in country_data["topics"]:
                for year_info in topic_data["num_articles_per_year"]:
                    country_topic_year = CountryTopicsYear(
                        topic_name=topic_data["topic_name"],
                        year=year_info["year"],
                        total_articles=year_info["num_articles"],
                    )
                    country_topic_year.save()

        for country_data in countries:
            for topic_data in country_data["topics"]:
                country_topic = CountryTopics(
                    topic_name=topic_data["topic_name"],
                    total_articles=topic_data["total_topic_articles"],
                )
                country_topic.save()

        for country_data in countries:
            for topic_data in country_data["topics"]:
                accumulated_articles = 0
                for year_info in sorted(
                    topic_data["num_articles_per_year"], key=lambda x: x["year"]
                ):
                    accumulated_articles += year_info["num_articles"]
                    country_topic_acumulated = CountryTopicsAcumulated(
                        topic_name=topic_data["topic_name"],
                        year=year_info["year"],
                        total_articles=accumulated_articles,
                    )
                    country_topic_acumulated.save()

    def populate_affiliation(self):
        affiliations_list = self.get_affiliations_dict()
        for affiliation_data in affiliations_list:
            scopus_id = affiliation_data["id_affiliation"]
            name = affiliation_data["name"]
            total_articles = affiliation_data["total_articles"]

            # Mapear Affiliation
            affiliation = Affiliation(
                scopus_id=scopus_id, name=name, total_articles=total_articles
            )
            affiliation.save()

            # Mapear AffiliationYear
            for year_data in affiliation_data["years"]:
                total_topics_year = len(
                    {
                        t["topic_name"]
                        for t in affiliation_data["topics"]
                        if any(
                            y["year"] == year_data["year"]
                            for y in t["num_articles_per_year"]
                        )
                    }
                )
                affiliation_year = AffiliationYear(
                    scopus_id=scopus_id,
                    name=name,
                    year=year_data["year"],
                    total_articles=year_data["num_articles"],
                    total_topics=total_topics_year,
                )
                affiliation_year.save()

            # Mapear AffiliationAcumulated
            acumulated_articles = 0
            acumulated_topics = set()
            for year_data in sorted(affiliation_data["years"], key=lambda x: x["year"]):
                acumulated_articles += year_data["num_articles"]
                topics_this_year = {
                    t["topic_name"]
                    for t in affiliation_data["topics"]
                    if any(
                        y["year"] == year_data["year"]
                        for y in t["num_articles_per_year"]
                    )
                }
                acumulated_topics.update(topics_this_year)
                affiliation_acumulated = AffiliationAcumulated(
                    scopus_id=scopus_id,
                    name=name,
                    year=year_data["year"],
                    total_articles=acumulated_articles,
                    total_topics=len(acumulated_topics),
                )
                affiliation_acumulated.save()

            # Mapeo para AffiliationTopicsYear, AffiliationTopicsAcumulated y AffiliationTopics
            topic_totals = {}
            for topic_data in affiliation_data["topics"]:
                topic_name = topic_data["topic_name"]
                acumulated_topic_articles = 0

                for year_data in topic_data["num_articles_per_year"]:
                    year = year_data["year"]

                    # AffiliationTopicsYear
                    affiliation_topics_year = AffiliationTopicsYear(
                        scopus_id=scopus_id,
                        name=name,
                        topic_name=topic_name,
                        year=year,
                        total_articles=year_data["num_articles"],
                    )
                    affiliation_topics_year.save()
                    acumulated_topic_articles += year_data["num_articles"]
                    # AffiliationTopicsAcumulated
                    # if topic_name not in counted_topics:
                    #     counted_topics.add(topic_name)
                    #     acumulated_topic_articles += year_data["num_articles"]
                    # else:
                    #     previous_acumulated = AffiliationTopicsAcumulated.objects.filter(scopus_id=scopus_id,
                    #                                                                      name=name,
                    #                                                                      topic_name=topic_name,
                    #                                                                      year__lt=year).order_by(
                    #         '-year').first()
                    #     if previous_acumulated:
                    #         acumulated_topic_articles = previous_acumulated.total_articles

                    affiliation_topics_acumulated = AffiliationTopicsAcumulated(
                        scopus_id=scopus_id,
                        name=name,
                        topic_name=topic_name,
                        year=year,
                        total_articles=acumulated_topic_articles,
                    )
                    affiliation_topics_acumulated.save()

                    # Actualizar el total de artículos del topic
                    if topic_name in topic_totals:
                        topic_totals[topic_name] += year_data["num_articles"]
                    else:
                        topic_totals[topic_name] = year_data["num_articles"]

                # Crear AffiliationTopics para el total de artículos de cada topic
                affiliation_topics = AffiliationTopics(
                    scopus_id=scopus_id,
                    name=name,
                    topic_name=topic_name,
                    total_articles=topic_totals[topic_name],
                )
                affiliation_topics.save()

    def get_affiliations_articles_dict(self):
        pass

    def get_affiliations_authors_dict(self):
        query = """
                            MATCH (ar:Article)-[b:BELONGS_TO]->(af:Affiliation)
                            OPTIONAL MATCH (ar)-[u:USES]->(t:Topic)
                            RETURN af.scopus_id, af.name, ar.scopus_id, ar.publication_date, t.name
                        """

    def get_affiliations_topics_dict(self):
        pass

    def get_affiliations_dict(self):
        query = """
                    MATCH (ar:Article)-[b:BELONGS_TO]->(af:Affiliation)
                    OPTIONAL MATCH (ar)-[u:USES]->(t:Topic)
                    RETURN af.scopus_id, af.name, ar.scopus_id, ar.publication_date, t.name
                """
        results, meta = db.cypher_query(query)

        af_scopus_ids = []
        af_names = []
        ar_scopus_ids = []
        ar_publication_dates = []
        topics = []

        for result in results:
            af_scopus_ids.append(result[0])
            af_names.append(result[1])
            ar_scopus_ids.append(result[2])
            ar_publication_dates.append(result[3])
            topics.append(result[4] if result[4] is not None else " ")

        years = extract_year(ar_publication_dates)

        affiliations_data = count_articles_per_year_affiliation(
            af_scopus_ids, af_names, ar_scopus_ids, years, topics
        )

        affiliations_list = []

        for affiliation_data in affiliations_data:
            # Crear diccionarios para YearContribution
            years = [
                {"year": year_info["year"], "num_articles": year_info["numArticles"]}
                for year_info in affiliation_data["years"]
            ]

            # Crear diccionarios para Topic
            topics = []
            for topic_data in affiliation_data["topics"]:
                num_articles_per_year = [
                    {
                        "year": year_info["year"],
                        "num_articles": year_info["numArticles"],
                    }
                    for year_info in topic_data["topic_years"]
                ]
                topic = {
                    "topic_name": topic_data["topic"],
                    "num_articles_per_year": num_articles_per_year,
                    "total_topic_articles": topic_data["totalTopicArticles"],
                }
                topics.append(topic)

            # Crear diccionario para Affiliation
            affiliation_dict = {
                "id_affiliation": affiliation_data["idScopus"],
                "name": affiliation_data["name"],
                "years": years,
                "topics": topics,
                "total_articles": affiliation_data["totalArticles"],
            }

            affiliations_list.append(affiliation_dict)

        return affiliations_list
