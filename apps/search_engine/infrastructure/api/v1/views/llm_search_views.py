from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.search_engine.application.services.llm_search_service import LLMSearchService


class LLMSearchViewSet(viewsets.ViewSet):
    _llm_search_service = None

    @property
    def llm_search_service(self):
        # Instanciacion perezosa: LLMSearchService carga modelos SciBERT/KeyBERT
        # pesados. Si esto se hace a nivel de clase (import time), cualquier
        # test que cargue el urlconf completo (via Django test client) crashea
        # aunque no toque este endpoint.
        if LLMSearchViewSet._llm_search_service is None:
            LLMSearchViewSet._llm_search_service = LLMSearchService()
        return LLMSearchViewSet._llm_search_service

    @extend_schema(
        summary="Search using LLM",
        description="Search articles using LLM-based semantic search",
        tags=["Search"],
    )
    @action(detail=False, methods=["post"], url_path="semantic-search")
    def semantic_search(self, request):
        try:
            query = request.data.get("query")
            if not query:
                return Response(
                    {"error": "Query is required"}, status=status.HTTP_400_BAD_REQUEST
                )
            # page = int(request.data.get('page', 1))
            # page_size = int(request.data.get('page_size', 10))
            top_k = request.data.get("top_k", 10)
            # page = request.data.get('page', 1)

            results = self.llm_search_service.search(query, top_k)

            # Results now come with all necessary fields from Neo4j
            transformed_results = []
            for result in results:
                transformed_results.append(
                    {
                        "title": result["title"],
                        "abstract": result["abstract"],
                        "author_count": result["author_count"],
                        "affiliation_count": result["affiliation_count"],
                        "publication_date": result["publication_date"],
                        "scopus_id": result["article_id"],
                        "authors": result["authors"],
                        "affiliations": result["affiliations"],
                        "relevance": result["relevance_score"],
                    }
                )

            response_data = {
                "data": transformed_results,
                "years": list(
                    set(
                        r["publication_date"].split("-")[0]
                        for r in results
                        if r["publication_date"]
                    )
                ),
                "total": len(results),
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
