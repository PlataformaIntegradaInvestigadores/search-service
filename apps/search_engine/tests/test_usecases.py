from unittest import TestCase
from unittest.mock import Mock

from apps.search_engine.application.usecases.affiliation.affiliations_by_authors_usecase import (
    AffiliationByAuthorsUsecase,
)
from apps.search_engine.application.usecases.affiliation.find_affiliation_by_id import (
    FindAffiliationByScopusIdIUseCase,
)
from apps.search_engine.application.usecases.affiliation.list_all_affiliation_usecase import (
    ListAllAffiliationsUseCase,
)
from apps.search_engine.application.usecases.affiliation.total_affiliations_usecase import (
    TotalAffiliationsUseCase,
)
from apps.search_engine.application.usecases.article.article_by_id_usecase import (
    ArticleByIdUseCase,
)
from apps.search_engine.application.usecases.article.articles_bulk_create_usecase import (
    ArticlesBulkCreateUseCase,
)
from apps.search_engine.application.usecases.article.list_all_articles_usecase import (
    ListAllArticlesUseCase,
)
from apps.search_engine.application.usecases.article.total_articles_usecase import (
    TotalArticlesUseCase,
)
from apps.search_engine.application.usecases.author.author_by_affiliations_filters import (
    AuthorsByAffiliationsFiltersUseCase,
)
from apps.search_engine.application.usecases.author.author_by_id_usecase import (
    AuthorByIdUseCase,
)
from apps.search_engine.application.usecases.author.author_by_query_usecase import (
    AuthorByQueryUseCase,
)
from apps.search_engine.application.usecases.author.author_community_use_case import (
    AuthorsCommunityUseCase,
)
from apps.search_engine.application.usecases.author.authors_bulk_create_usecase import (
    AuthorsBulkCreateUseCase,
)
from apps.search_engine.application.usecases.author.list_all_authors_usecase import (
    ListAllAuthorsUseCase,
)
from apps.search_engine.application.usecases.author.most_relevant_authors_by_topic import (
    MostRelevantAuthorsByTopicUseCase,
)
from apps.search_engine.application.usecases.author.retrieve_author_usecase import (
    RetrieveAuthorUseCase,
)
from apps.search_engine.application.usecases.coauthored.find_coauthors_by_id_usecase import (
    FindCoauthorsByIdUsecase,
)
from apps.search_engine.application.usecases.summary.get_summary_usecase import (
    GetSummaryUseCase,
)
from apps.search_engine.application.usecases.topic.list_all_topics_usecase import (
    ListAllTopicsUseCase,
)


class UseCaseDelegationTests(TestCase):
    """Every use case is a thin repository wrapper; verify the delegation."""

    def test_affiliation_by_authors(self):
        repo = Mock()
        repo.find_affiliations_by_authors.return_value = ["a"]
        result = AffiliationByAuthorsUsecase(repo).execute(["u1"])
        repo.find_affiliations_by_authors.assert_called_once_with(["u1"])
        self.assertEqual(result, ["a"])

    def test_find_affiliation_by_id(self):
        repo = Mock()
        repo.find_by_id.return_value = "aff"
        result = FindAffiliationByScopusIdIUseCase(repo).execute("1")
        repo.find_by_id.assert_called_once_with("1")
        self.assertEqual(result, "aff")

    def test_list_all_affiliations(self):
        repo = Mock()
        repo.find_all.return_value = ["a"]
        result = ListAllAffiliationsUseCase(repo).execute(page_number=2, page_size=5)
        repo.find_all.assert_called_once_with(page_number=2, page_size=5)
        self.assertEqual(result, ["a"])

    def test_total_affiliations(self):
        repo = Mock()
        repo.find_total_affiliations.return_value = 3
        self.assertEqual(TotalAffiliationsUseCase(repo).execute(), 3)

    def test_article_by_id(self):
        repo = Mock()
        repo.find_by_id.return_value = "article"
        self.assertEqual(ArticleByIdUseCase(repo).execute("1"), "article")

    def test_articles_bulk_create(self):
        repo = Mock()
        repo.bulk_create.return_value = ["x"]
        result = ArticlesBulkCreateUseCase(repo).execute([{"a": 1}])
        repo.bulk_create.assert_called_once_with([{"a": 1}])
        self.assertEqual(result, ["x"])

    def test_list_all_articles(self):
        repo = Mock()
        repo.find_all.return_value = ["a"]
        result = ListAllArticlesUseCase(repo).execute(1, 10)
        repo.find_all.assert_called_once_with(1, 10)
        self.assertEqual(result, ["a"])

    def test_total_articles(self):
        repo = Mock()
        repo.find_total_articles.return_value = 7
        self.assertEqual(TotalArticlesUseCase(repo).execute(), 7)

    def test_authors_by_affiliations_filters(self):
        repo = Mock()
        repo.find_authors_by_affiliation_filter.return_value = ["a"]
        result = AuthorsByAffiliationsFiltersUseCase(repo).execute(
            "include", ["aff1"], ["au1"]
        )
        repo.find_authors_by_affiliation_filter.assert_called_once_with(
            "include", ["aff1"], ["au1"]
        )
        self.assertEqual(result, ["a"])

    def test_author_by_id(self):
        repo = Mock()
        repo.find_by_id.return_value = "author"
        self.assertEqual(AuthorByIdUseCase(repo).execute("1"), "author")

    def test_author_by_query(self):
        repo = Mock()
        repo.find_authors_by_query.return_value = (["a"], 1)
        result = AuthorByQueryUseCase(repo).execute(name="ana", page_size=10, page=1)
        repo.find_authors_by_query.assert_called_once_with(
            "ana", page_size=10, page=1
        )
        self.assertEqual(result, (["a"], 1))

    def test_authors_community(self):
        repo = Mock()
        repo.find_community.return_value = {"nodes": []}
        result = AuthorsCommunityUseCase(repo).execute(["a1"])
        repo.find_community.assert_called_once_with(["a1"])
        self.assertEqual(result, {"nodes": []})

    def test_authors_bulk_create_passes_list_not_unpacked(self):
        repo = Mock()
        repo.bulk_create.return_value = ["a", "b"]
        authors = [{"scopus_id": "1"}, {"scopus_id": "2"}]
        result = AuthorsBulkCreateUseCase(repo).execute(authors)
        repo.bulk_create.assert_called_once_with(authors)
        self.assertEqual(result, ["a", "b"])

    def test_list_all_authors(self):
        repo = Mock()
        repo.find_all.return_value = ["a"]
        result = ListAllAuthorsUseCase(repo).execute(page_size=5, page=2)
        repo.find_all.assert_called_once_with(page_size=5, page=2)
        self.assertEqual(result, ["a"])

    def test_most_relevant_authors_by_topic(self):
        repo = Mock()
        repo.find_most_relevant_authors_by_topic.return_value = ["a"]
        result = MostRelevantAuthorsByTopicUseCase(repo).execute("ai", 5)
        repo.find_most_relevant_authors_by_topic.assert_called_once_with("ai", 5)
        self.assertEqual(result, ["a"])

    def test_retrieve_author(self):
        repo = Mock()
        repo.find_by_id.return_value = "author"
        self.assertEqual(RetrieveAuthorUseCase(repo).execute(1), "author")

    def test_find_coauthors_by_id(self):
        repo = Mock()
        repo.find_coauthors_by_id.return_value = (["a"], ["l"])
        result = FindCoauthorsByIdUsecase(repo).execute("1")
        repo.find_coauthors_by_id.assert_called_once_with("1")
        self.assertEqual(result, (["a"], ["l"]))

    def test_get_summary(self):
        article_repo, author_repo, topic_repo = Mock(), Mock(), Mock()
        article_repo.articles_count.return_value = 1
        author_repo.authors_count.return_value = 2
        topic_repo.topics_count.return_value = 3
        result = GetSummaryUseCase(article_repo, author_repo, topic_repo).execute()
        self.assertEqual(result, {"authors": 2, "topics": 3, "articles": 1})

    def test_list_all_topics(self):
        repo = Mock()
        repo.find_all.return_value = ["t"]
        self.assertEqual(ListAllTopicsUseCase(repo).execute(), ["t"])
