from drf_spectacular.utils import OpenApiParameter, extend_schema
from mongoengine import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.dashboards.application.services.country_service import CountryService
from apps.dashboards.application.use_cases.country_acumulated_use_case import (
    CountryAcumulatedUseCase,
)
from apps.dashboards.application.use_cases.country_topics_acumulated_use_case import (
    CountryTopicsAcumulatedUseCase,
)
from apps.dashboards.application.use_cases.country_topics_use_case import (
    CountryTopicsUseCase,
)
from apps.dashboards.application.use_cases.country_year_use_case import (
    CountryYearUseCase,
)
from apps.dashboards.application.use_cases.get_range_use_case import RangeUseCase
from apps.dashboards.application.use_cases.last_years_use_case import LastYearsUseCase
from apps.dashboards.application.use_cases.top_topics_by_year import (
    TopTopicsByYearUseCase,
)
from apps.dashboards.application.use_cases.top_topics_use_case import TopTopicsUseCase
from apps.dashboards.application.use_cases.year_info_use_case import YearInfoUseCase
from apps.dashboards.domain.entities.affiliation_topics import AffiliationTopics
from apps.dashboards.domain.entities.affiliation_topics_acumulated import (
    AffiliationTopicsAcumulated,
)
from apps.dashboards.domain.entities.affiliation_topics_year import (
    AffiliationTopicsYear,
)
from apps.dashboards.domain.entities.country_topics import CountryTopics
from apps.dashboards.domain.entities.country_topics_acumulated import (
    CountryTopicsAcumulated,
)
from apps.dashboards.domain.entities.country_topics_year import CountryTopicsYear
from apps.dashboards.infrastructure.api.v1.serializers.affiliation_topic_serializer import (
    AffiliationTopicYearSerializer,
)
from apps.dashboards.infrastructure.api.v1.serializers.affiliation_topics_acumulated_serializer import (
    AffiliationTopicAcumulatedSerializer,
)
from apps.dashboards.infrastructure.api.v1.serializers.affiliation_topics_serializer import (
    AffiliationTopicsSerializer,
)
from apps.dashboards.infrastructure.api.v1.serializers.country_acumulated_serializer import (
    CountryAcumulatedSerializer,
)
from apps.dashboards.infrastructure.api.v1.serializers.country_topics_serializer import (
    CountryTopicsSerializer,
)
from apps.dashboards.infrastructure.api.v1.serializers.country_topics_year_serializer import (
    CountryTopicsYearSerializer,
)
from apps.dashboards.infrastructure.api.v1.serializers.country_year_serializer import (
    CountryYearSerializer,
)


class CountryViews(viewsets.ModelViewSet):
    country_service = CountryService()

    @extend_schema(
        description="Get topics for a country",
        responses=CountryTopicsSerializer(many=True),
        tags=["Countries"],
        parameters=[
            OpenApiParameter(
                name="number_top",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Number of top topics",
            )
        ],
    )
    @action(detail=False, methods=["get"])
    def get_topics(self, request):
        try:
            number_top = request.query_params.get("number_top")
            country_topics = CountryTopicsUseCase(country_service=self.country_service)
            data_topics = country_topics.execute(number_top=number_top)
            topics = CountryTopicsSerializer(data_topics, many=True)
            data = topics.data
            response_data = [
                {"text": topic["topic_name"], "size": topic["total_articles"]}
                for topic in data
            ]
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get accumulated topics for a country",
        responses=CountryTopicsSerializer(many=True),
        tags=["Countries"],
        parameters=[
            OpenApiParameter(
                name="topic",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Topic name",
            ),
            OpenApiParameter(
                name="year",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Year",
            ),
        ],
    )
    @action(detail=False, methods=["get"])
    def get_topics_acumulated(self, request):
        try:
            topic = request.query_params.get("topic")
            year = request.query_params.get("year")
            country_topics_acumulated = CountryTopicsAcumulatedUseCase(
                country_service=self.country_service
            )
            data_topics = country_topics_acumulated.execute(topic=topic, year=year)
            topics = CountryTopicsSerializer(data_topics, many=True)
            return Response(topics.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get accumulated data for a country by year",
        responses=CountryAcumulatedSerializer,
        tags=["Countries"],
        parameters=[
            OpenApiParameter(
                name="year",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Year",
            )
        ],
    )
    @action(detail=False, methods=["get"])
    def get_acumulated(self, request):
        try:
            year = request.query_params.get("year", 2023)
            country_acumulated = CountryAcumulatedUseCase(
                country_service=self.country_service
            )
            data_topics = country_acumulated.execute(year=year)
            serializer = CountryAcumulatedSerializer(data_topics, many=False)
            data = serializer.data
            response_data = {
                "author": data["total_authors"],
                "article": data["total_articles"],
                "affiliation": data["total_affiliations"],
                "topic": data["total_topics"],
            }
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get data for a country by year",
        responses=CountryYearSerializer,
        tags=["Countries"],
        parameters=[
            OpenApiParameter(
                name="year",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Year",
            )
        ],
    )
    @action(detail=False, methods=["get"])
    def get_year(self, request):
        try:
            year = request.query_params.get("year")
            year_use_case = CountryYearUseCase(country_service=self.country_service)
            year_response = year_use_case.execute(year)
            serializer = CountryYearSerializer(year_response)
            data = serializer.data
            response_data = {
                "author": data["total_authors"],
                "article": data["total_articles"],
                "affiliation": data["total_affiliations"],
                "topic": data["total_topics"],
            }
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get top topics for a country by year",
        responses=CountryTopicsSerializer(many=True),
        tags=["Countries"],
        parameters=[
            OpenApiParameter(
                name="year",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Year",
            )
        ],
    )
    @action(detail=False, methods=["get"])
    def get_top_topics(self, request):
        try:
            year = request.query_params.get("year")
            top_topics_use_case = TopTopicsUseCase(country_service=self.country_service)
            top_topics = top_topics_use_case.execute(year=year)
            serializer = CountryTopicsSerializer(top_topics, many=True)
            data = serializer.data
            response_data = [
                {"text": topic["topic_name"], "size": topic["total_articles"]}
                for topic in data
            ]
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get top topics for a country by year",
        responses=CountryTopicsYearSerializer(many=True),
        tags=["Countries"],
        parameters=[
            OpenApiParameter(
                name="year",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Year",
            )
        ],
    )
    @action(detail=False, methods=["get"])
    def get_top_topics_year(self, request):
        try:
            year = request.query_params.get("year")
            top_topics_by_year_use_case = TopTopicsByYearUseCase(
                country_service=self.country_service
            )
            top_by_year = top_topics_by_year_use_case.execute(year=year)
            serializer = CountryTopicsYearSerializer(top_by_year, many=True)
            data = serializer.data
            response_data = [
                {"text": topic["topic_name"], "size": topic["total_articles"]}
                for topic in data
            ]
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get data for the last years for a country",
        responses=CountryYearSerializer(many=True),
        tags=["Countries"],
    )
    @action(detail=False, methods=["get"])
    def get_last_years(self, request):
        try:
            last_years_use_case = LastYearsUseCase(country_service=self.country_service)
            last_years = last_years_use_case.execute()
            serializer = CountryYearSerializer(last_years, many=True)
            data = serializer.data
            response_data = [
                {
                    "year": cy["year"],
                    "author": cy["total_authors"],
                    "article": cy["total_articles"],
                    "affiliation": cy["total_affiliations"],
                    "topic": cy["total_topics"],
                }
                for cy in data
            ]
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get years with data for a country",
        responses=CountryYearSerializer(many=True),
        tags=["Countries"],
    )
    @action(detail=False, methods=["get"])
    def get_years(self, request):
        try:
            years_use_case = LastYearsUseCase(country_service=self.country_service)
            last_years = years_use_case.execute()
            serializer = CountryYearSerializer(last_years, many=True)
            data = serializer.data
            response_data = [
                {
                    "year": cy["year"],
                }
                for cy in data
            ]
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get detailed information for a specific year for a country",
        responses=CountryYearSerializer,
        tags=["Countries"],
        parameters=[
            OpenApiParameter(
                name="year",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Year",
            )
        ],
    )
    @action(detail=False, methods=["get"])
    def get_year_info(self, request):
        try:
            year = request.query_params.get("year")
            year_info_use_case = YearInfoUseCase(country_service=self.country_service)
            year_info = year_info_use_case.execute(year=year)
            serializer = CountryYearSerializer(year_info)
            cy = serializer.data
            response_data = [
                {
                    "year": cy["year"],
                    "author": cy["total_authors"],
                    "article": cy["total_articles"],
                    "affiliation": cy["total_affiliations"],
                    "topic": cy["total_topics"],
                }
            ]
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get information for a range of years for a country",
        responses=CountryYearSerializer(many=True),
        tags=["Countries"],
        parameters=[
            OpenApiParameter(
                name="year",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Year",
            )
        ],
    )
    @action(detail=False, methods=["get"])
    def get_range_info(self, request):
        try:
            year = request.query_params.get("year")
            range_use_case = RangeUseCase(country_service=self.country_service)
            year_info = range_use_case.execute(year=year)
            serializer = CountryYearSerializer(year_info, many=True)
            data = serializer.data
            response_data = [
                {
                    "year": cy["year"],
                    "author": cy["total_authors"],
                    "article": cy["total_articles"],
                    "affiliation": cy["total_affiliations"],
                    "topic": cy["total_topics"],
                }
                for cy in data
            ]
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    ##########Topics dashboard functions#############

    @extend_schema(
        description="Search topics by query",
        responses=CountryTopicsSerializer(many=True),
        tags=["Topics"],
        parameters=[
            OpenApiParameter(
                name="query",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Search query",
            )
        ],
    )
    @action(detail=False, methods=["get"])
    def search(self, request):
        try:
            query = request.GET.get("query", "")
            topics = CountryTopics.objects.filter(
                Q(topic_name__icontains=query)
            ).order_by("-total_articles")[:20]
            result = [
                {"name": topic.topic_name, "total_articles": topic.total_articles}
                for topic in topics
            ]
            return Response(result)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get topics for a country by year",
        responses=CountryTopicsYearSerializer(many=True),
        tags=["Topics"],
        parameters=[
            OpenApiParameter(
                name="topic",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Topic name",
            )
        ],
    )
    @action(detail=False, methods=["get"])
    def get_topics_years(self, request):
        try:
            name = request.query_params.get("topic")
            topic_info = (
                CountryTopicsYear.objects(topic_name=name)
                .filter(year__gt=1999)
                .order_by("year")
            )
            serializer = CountryTopicsYearSerializer(topic_info, many=True)
            data = serializer.data
            response_data = [
                {
                    "year": topic["year"],
                }
                for topic in data
            ]
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get affiliations by topic",
        responses=AffiliationTopicsSerializer(many=True),
        tags=["Topics"],
        parameters=[
            OpenApiParameter(
                name="topic",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Topic name",
            )
        ],
    )
    @action(detail=False, methods=["get"])
    def get_topics_affiliations(self, request):
        try:
            name = request.query_params.get("topic")
            topic_info = AffiliationTopics.objects(topic_name=name).order_by(
                "-total_articles"
            )[:30]
            serializer = AffiliationTopicsSerializer(topic_info, many=True)
            data = serializer.data
            response_data = [
                {"text": affiliation["name"], "size": affiliation["total_articles"]}
                for affiliation in data
            ]
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get affiliations by topic and year",
        responses=AffiliationTopicYearSerializer(many=True),
        tags=["Topics"],
        parameters=[
            OpenApiParameter(
                name="topic",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Topic name",
            ),
            OpenApiParameter(
                name="year",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Year",
            ),
        ],
    )
    @action(detail=False, methods=["get"])
    def get_topics_affiliations_year(self, request):
        try:
            name = request.query_params.get("topic")
            year = request.query_params.get("year")
            topic_info = (
                AffiliationTopicsYear.objects(topic_name=name)
                .filter(year=year)
                .order_by("-total_articles")[:30]
            )
            serializer = AffiliationTopicYearSerializer(topic_info, many=True)
            data = serializer.data
            response_data = [
                {"text": affiliation["name"], "size": affiliation["total_articles"]}
                for affiliation in data
            ]
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get accumulated affiliations by topic and year",
        responses=AffiliationTopicAcumulatedSerializer(many=True),
        tags=["Topics"],
        parameters=[
            OpenApiParameter(
                name="topic",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Topic name",
            ),
            OpenApiParameter(
                name="year",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Year",
            ),
        ],
    )
    @action(detail=False, methods=["get"])
    def get_topics_affiliations_acumulated(self, request):
        try:
            name = request.query_params.get("topic")
            year = request.query_params.get("year")
            topic_info = (
                AffiliationTopicsAcumulated.objects(topic_name=name)
                .filter(year=year)
                .order_by("-total_articles")[:30]
            )
            serializer = AffiliationTopicAcumulatedSerializer(topic_info, many=True)
            data = serializer.data
            response_data = [
                {"text": affiliation["name"], "size": affiliation["total_articles"]}
                for affiliation in data
            ]
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get topics by year for a country",
        responses=CountryTopicsYearSerializer(many=True),
        tags=["Topics"],
        parameters=[
            OpenApiParameter(
                name="topic",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Topic name",
            )
        ],
    )
    @action(detail=False, methods=["get"])
    def get_topics_year_info(self, request):
        try:
            topic = request.query_params.get("topic")
            years = (
                CountryTopicsYear.objects(topic_name=topic)
                .filter(year__gt=1999)
                .order_by("year")
            )
            serializer = CountryTopicsYearSerializer(years, many=True)
            data = serializer.data
            return Response(data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get topic information by year for a country",
        responses=CountryTopicsYearSerializer,
        tags=["Topics"],
        parameters=[
            OpenApiParameter(
                name="topic",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Topic name",
            ),
            OpenApiParameter(
                name="year",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Year",
            ),
        ],
    )
    @action(detail=False, methods=["get"])
    def get_topics_year(self, request):
        try:
            topic = request.query_params.get("topic")
            year = request.query_params.get("year")
            years = CountryTopicsYear.objects.get(topic_name=topic, year=year)
            serializer = CountryTopicsYearSerializer(years)
            data = serializer.data
            return Response([data])
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get topic information for a range of years for a country",
        responses=CountryTopicsYearSerializer(many=True),
        tags=["Topics"],
        parameters=[
            OpenApiParameter(
                name="topic",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Topic name",
            ),
            OpenApiParameter(
                name="year",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Year",
            ),
        ],
    )
    @action(detail=False, methods=["get"])
    def get_topics_range_year(self, request):
        try:
            topic = request.query_params.get("topic")
            year = request.query_params.get("year")
            years = (
                CountryTopicsYear.objects(topic_name=topic)
                .filter(year__gt=1999, year__lte=year)
                .order_by("year")
            )
            serializer = CountryTopicsYearSerializer(years, many=True)
            data = serializer.data
            return Response(data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get topic summary for a country",
        responses=CountryTopicsSerializer,
        tags=["Topics"],
        parameters=[
            OpenApiParameter(
                name="topic",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Topic name",
            )
        ],
    )
    @action(detail=False, methods=["get"])
    def get_topics_summary(self, request):
        try:
            topic = request.query_params.get("topic")
            years = CountryTopics.objects.get(topic_name=topic)
            serializer = CountryTopicsSerializer(years)
            data = serializer.data
            affiliations = AffiliationTopics.objects(topic_name=topic).count()
            response_data = {
                "articles": data["total_articles"],
                "affiliations": affiliations,
            }
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get topic summary for a country by year",
        responses=CountryTopicsYearSerializer,
        tags=["Topics"],
        parameters=[
            OpenApiParameter(
                name="topic",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Topic name",
            ),
            OpenApiParameter(
                name="year",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Year",
            ),
        ],
    )
    @action(detail=False, methods=["get"])
    def get_topics_summary_year(self, request):
        try:
            topic = request.query_params.get("topic")
            year = request.query_params.get("year")
            years = CountryTopicsYear.objects.get(topic_name=topic, year=year)
            serializer = CountryTopicsYearSerializer(years)
            data = serializer.data
            affiliations = AffiliationTopicsYear.objects(
                topic_name=topic, year=year
            ).count()
            response_data = {
                "articles": data["total_articles"],
                "affiliations": affiliations,
            }
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get accumulated topic summary for a country by year",
        responses=CountryTopicsYearSerializer,
        tags=["Topics"],
        parameters=[
            OpenApiParameter(
                name="topic",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Topic name",
            ),
            OpenApiParameter(
                name="year",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Year",
            ),
        ],
    )
    @action(detail=False, methods=["get"])
    def get_topics_summary_acumulated(self, request):
        try:
            topic = request.query_params.get("topic")
            year = request.query_params.get("year")
            years = CountryTopicsAcumulated.objects.get(topic_name=topic, year=year)
            serializer = CountryTopicsYearSerializer(years)
            data = serializer.data
            aff = AffiliationTopicsAcumulated.objects(topic_name=topic).filter(
                year__lte=year
            )
            unique_scopus_ids = len(aff.distinct("scopus_id"))
            response_data = {
                "articles": data["total_articles"],
                "affiliations": unique_scopus_ids,
            }
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

