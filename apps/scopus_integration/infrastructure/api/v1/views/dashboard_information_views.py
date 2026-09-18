from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.dashboards.domain.entities.affiliation import Affiliation as MongoAffiliation
from apps.dashboards.domain.entities.author import Author as MongoAuthor
from apps.dashboards.domain.entities.country_acumulated import CountryAcumulated
from apps.dashboards.domain.entities.country_topics import CountryTopics
from apps.scopus_integration.application.services.model_corpus_observer_service import (
    ModelCorpusObserverService,
)
from apps.scopus_integration.application.services.search_scopus_service import (
    RetrieveScopusData,
)
from apps.search_engine.application.services.affiliation_service import (
    AffiliationService,
)
from apps.search_engine.application.services.article_service import ArticleService
from apps.search_engine.application.services.author_service import AuthorService
from apps.search_engine.application.services.topic_service import TopicService


class DashboardInformationViewSet(viewsets.ViewSet):
    author_service = AuthorService()
    article_service = ArticleService()
    affiliation_service = AffiliationService()
    topic_service = TopicService()
    retrieve_scopus_data = RetrieveScopusData()
    model_corpus_observer = ModelCorpusObserverService()

    @extend_schema(
        summary="Get the total number of authors",
        description="This endpoint returns the total number of authors in the system.",
        tags=["Dashboard Information"],
    )
    @action(detail=False, methods=["get"], url_path="get_authors_comparator")
    def get_authors_comparator(self, request, *args, **kwargs):
        try:
            authors_no_updated = self.author_service.get_authors_no_updated_count()
            total_authors = self.author_service.authors_count()
            return Response(
                {
                    "authors_no_updated": authors_no_updated,
                    "total_authors": total_authors,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Get the total number of articles",
        description="This endpoint returns the total number of articles in the system.",
        tags=["Dashboard Information"],
    )
    @action(detail=False, methods=["get"], url_path="get_articles_comparator")
    def get_articles_comparator(self, request, *args, **kwargs):
        try:
            total_articles_centinela = self.article_service.articles_count()
            total_articles_scopus = (
                self.retrieve_scopus_data.get_total_articles_from_scopus()
            )
            return Response(
                {
                    "total_centinela": total_articles_centinela,
                    "total_scopus": int(total_articles_scopus),
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Verify if model and corpus paths exist",
        description="This endpoint returns if the model and corpus paths exist.",
        tags=["Dashboard Information"],
    )
    @action(detail=False, methods=["get"], url_path="tfidf_model_corpus")
    def tfidf_model_corpus(self, request):
        try:
            model_exists = self.model_corpus_observer.verify_model_path_exists()
            corpus_exists = self.model_corpus_observer.verify_corpus_path_exists()
            return Response(
                {"model": model_exists, "corpus": corpus_exists},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Estado de salud de la sincronización Neo4j → MongoDB",
        description=(
            "Compara los totales de la fuente de verdad (Neo4j) contra los agregados "
            "ya materializados en MongoDB por el ETL incremental, para detectar autores "
            "sin métricas, artículos pendientes de sincronizar y colecciones desactualizadas."
        ),
        tags=["Dashboard Information"],
    )
    @action(detail=False, methods=["get"], url_path="get_system_health")
    def get_system_health(self, request):
        try:
            authors_no_updated = self.author_service.get_authors_no_updated_count()

            neo4j_authors = self.author_service.authors_count()
            neo4j_articles = self.article_service.articles_count()
            neo4j_affiliations = self.affiliation_service.find_total_affiliations()
            neo4j_topics = self.topic_service.topics_count()

            mongo_authors = MongoAuthor.objects.count()
            mongo_affiliations = MongoAffiliation.objects.count()
            mongo_topics = (
                CountryTopics.objects.filter(topic_name__ne=" ")
                .filter(topic_name__ne="")
                .count()
            )
            latest_acumulated = CountryAcumulated.objects.order_by("-year").first()
            mongo_articles = (
                latest_acumulated.total_articles if latest_acumulated else 0
            )

            articles_pending = max(0, neo4j_articles - mongo_articles)

            stale_collections = []
            if neo4j_authors != mongo_authors:
                stale_collections.append("author")
            if neo4j_affiliations != mongo_affiliations:
                stale_collections.append("affiliation")
            if neo4j_topics != mongo_topics:
                stale_collections.append("country_topics")
            if neo4j_articles != mongo_articles:
                stale_collections.append("country_acumulated")

            return Response(
                {
                    "authors_no_updated": authors_no_updated,
                    "total_authors": neo4j_authors,
                    "articles_pending": articles_pending,
                    "stale_collections": len(stale_collections),
                    "stale_collection_names": stale_collections,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
