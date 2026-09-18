from unittest import TestCase
from unittest.mock import Mock

import pandas as pd

from apps.search_engine.application.usecases.article.most_relevant_articles_by_topic_usecase import (
    MostRelevantArticlesUseCase,
)


class MostRelevantArticlesUseCaseTest(TestCase):
    def setUp(self) -> None:
        self.repository = Mock()
        self.repository.find_years_by_articles.return_value = [
            "2024-01-01",
            "2023-01-01",
        ]
        self.use_case = MostRelevantArticlesUseCase(self.repository)

    def test_accepts_enriched_article_list_from_current_repository(self) -> None:
        self.repository.find_most_relevant_articles_by_topic.return_value = [
            {"scopus_id": "A-1", "relevance": 0.91, "title": "First"},
            {"scopus_id": "A-2", "relevance": 0.73, "title": "Second"},
        ]

        articles, years = self.use_case.execute("smart grids", page=1, size=10)

        self.assertEqual(
            articles,
            [
                {"scopus_id": "A-1", "relevance": 0.91},
                {"scopus_id": "A-2", "relevance": 0.73},
            ],
        )
        self.assertEqual(years, ["2024-01-01", "2023-01-01"])
        self.repository.find_years_by_articles.assert_called_once_with(["A-1", "A-2"])

    def test_remains_compatible_with_legacy_pandas_series(self) -> None:
        self.repository.find_most_relevant_articles_by_topic.return_value = pd.Series(
            [0.91, 0.73],
            index=["A-1", "A-2"],
        )

        articles, _ = self.use_case.execute("smart grids", page=1, size=10)

        self.assertEqual(
            articles,
            [
                {"scopus_id": "A-1", "relevance": 0.91},
                {"scopus_id": "A-2", "relevance": 0.73},
            ],
        )
