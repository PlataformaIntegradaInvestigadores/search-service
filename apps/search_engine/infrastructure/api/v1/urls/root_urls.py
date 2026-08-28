from django.urls import include, path

from apps.search_engine.infrastructure.api.v1.views.summary_views import SummaryView

urlpatterns = [
    path(
        "authors/",
        include("apps.search_engine.infrastructure.api.v1.urls.author_urls"),
        name="authors",
    ),
    path(
        "articles/",
        include("apps.search_engine.infrastructure.api.v1.urls.article_urls"),
        name="articles",
    ),
    path(
        "topics/",
        include("apps.search_engine.infrastructure.api.v1.urls.topic_urls"),
        name="topics",
    ),
    path(
        "affiliations/",
        include("apps.search_engine.infrastructure.api.v1.urls.affiliation_urls"),
        name="affiliations",
    ),
    path(
        "coauthors/",
        include("apps.search_engine.infrastructure.api.v1.urls.coauthor_urls"),
        name="coauthors",
    ),
    path("summary/", SummaryView.as_view(), name="summary"),
    path('llm-search/', include('apps.search_engine.infrastructure.api.v1.urls.llm_search_urls')),  # Modified this line
]
