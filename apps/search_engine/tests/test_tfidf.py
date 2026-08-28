from unittest.mock import MagicMock, mock_open, patch

from django.test import SimpleTestCase

from apps.search_engine.application.utils.tfidf import Model


def _make_model(model_type="article", fake_model=None):
    Model._nlp = None
    Model._kw_model = None
    with patch(
        "apps.search_engine.application.utils.tfidf.open",
        mock_open(read_data=b""),
    ), patch(
        "apps.search_engine.application.utils.tfidf.pickle.load",
        return_value=fake_model or {},
    ), patch(
        "apps.search_engine.application.utils.tfidf.spacy.load"
    ), patch(
        "apps.search_engine.application.utils.tfidf.KeyBERT"
    ), patch(
        "apps.search_engine.application.utils.tfidf.GoogleTranslator"
    ):
        return Model(model_type)


class ModelLoadTests(SimpleTestCase):
    def test_load_model_rejects_non_string_type(self):
        with self.assertRaises(Exception):
            _make_model(model_type=123)

    def test_load_model_uses_tfidf_path_for_article(self):
        with patch(
            "apps.search_engine.application.utils.tfidf.open",
            mock_open(read_data=b""),
        ) as mocked_open, patch(
            "apps.search_engine.application.utils.tfidf.pickle.load", return_value={}
        ), patch("apps.search_engine.application.utils.tfidf.spacy.load"), patch(
            "apps.search_engine.application.utils.tfidf.KeyBERT"
        ), patch(
            "apps.search_engine.application.utils.tfidf.GoogleTranslator"
        ):
            Model("article")
        opened_path = mocked_open.call_args[0][0]
        self.assertIn("tf-idf/model-v10.0.pkl", opened_path)

    def test_load_model_uses_alternate_path_for_other_types(self):
        with patch(
            "apps.search_engine.application.utils.tfidf.open",
            mock_open(read_data=b""),
        ) as mocked_open, patch(
            "apps.search_engine.application.utils.tfidf.pickle.load", return_value={}
        ), patch("apps.search_engine.application.utils.tfidf.spacy.load"), patch(
            "apps.search_engine.application.utils.tfidf.KeyBERT"
        ), patch(
            "apps.search_engine.application.utils.tfidf.GoogleTranslator"
        ):
            Model("topic")
        opened_path = mocked_open.call_args[0][0]
        self.assertIn("model-v11.0.pkl", opened_path)

    def test_load_model_wraps_errors(self):
        with patch(
            "apps.search_engine.application.utils.tfidf.open",
            side_effect=FileNotFoundError("nope"),
        ), patch("apps.search_engine.application.utils.tfidf.spacy.load"), patch(
            "apps.search_engine.application.utils.tfidf.KeyBERT"
        ), patch(
            "apps.search_engine.application.utils.tfidf.GoogleTranslator"
        ):
            with self.assertRaises(Exception):
                Model("article")

    def test_nlp_and_kw_model_are_cached_singletons(self):
        Model._nlp = None
        Model._kw_model = None
        with patch(
            "apps.search_engine.application.utils.tfidf.open",
            mock_open(read_data=b""),
        ), patch(
            "apps.search_engine.application.utils.tfidf.pickle.load", return_value={}
        ), patch(
            "apps.search_engine.application.utils.tfidf.spacy.load"
        ) as mock_spacy_load, patch(
            "apps.search_engine.application.utils.tfidf.KeyBERT"
        ) as mock_keybert, patch(
            "apps.search_engine.application.utils.tfidf.GoogleTranslator"
        ):
            Model("article")
            Model("article")
        mock_spacy_load.assert_called_once()
        mock_keybert.assert_called_once()


class ModelQueryProcessingTests(SimpleTestCase):
    def setUp(self):
        self.model = _make_model()
        self.model.nlp = MagicMock()
        self.model.kw_model = MagicMock()
        self.model.translator = MagicMock()

    def test_detect_language_returns_detected_language(self):
        with patch(
            "apps.search_engine.application.utils.tfidf.detect", return_value="en"
        ):
            self.assertEqual(self.model.detect_language("hello"), "en")

    def test_detect_language_defaults_to_spanish_on_error(self):
        with patch(
            "apps.search_engine.application.utils.tfidf.detect",
            side_effect=Exception("boom"),
        ):
            self.assertEqual(self.model.detect_language(""), "es")

    def test_clean_text_strips_accents_and_punctuation(self):
        cleaned = self.model.clean_text("Café-Niño!")
        self.assertEqual(cleaned, "cafe nino")

    def test_enhance_query_semantically_short_query_unchanged(self):
        self.assertEqual(self.model.enhance_query_semantically("a b"), "a b")

    def test_enhance_query_semantically_uses_keywords_and_tokens(self):
        token = MagicMock(is_alpha=True, text="quantum")
        self.model.nlp.return_value = [token]
        self.model.kw_model.extract_keywords.return_value = [("quantum computing", 0.9)]
        result = self.model.enhance_query_semantically("quantum computing research topic")
        self.assertIn("quantum", result)

    def test_process_query_translates_non_english(self):
        with patch.object(self.model, "detect_language", return_value="es"):
            self.model.translator.translate.return_value = "hello world"
            with patch.object(
                self.model, "enhance_query_semantically", return_value="hello world"
            ):
                result = self.model.process_query("hola mundo")
        self.assertEqual(result, "hello world")

    def test_process_query_skips_translation_for_english(self):
        with patch.object(self.model, "detect_language", return_value="en"):
            with patch.object(
                self.model, "enhance_query_semantically", return_value="hello"
            ):
                result = self.model.process_query("hello")
        self.model.translator.translate.assert_not_called()
        self.assertEqual(result, "hello")

    def test_preprocess_topic_filters_stopwords_and_short_tokens(self):
        with patch.object(self.model, "process_query", return_value="the ai research"):
            tokens = self.model.preprocess_topic("ai research")
        self.assertNotIn("the", tokens)


class ModelRelevanceTests(SimpleTestCase):
    def test_returns_empty_series_when_no_valid_tokens(self):
        model = _make_model(fake_model={"vocabulary": {}})
        with patch.object(model, "preprocess_topic", return_value=["unknown"]):
            result = model.get_most_relevant_docs_by_topic_v2("unknown", None)
        self.assertTrue(result.empty)

    def test_computes_scores_for_valid_tokens(self):
        import numpy as np
        from scipy.sparse import csr_matrix

        matrix = csr_matrix(np.array([[1], [3]]))
        fake_model = {
            "vocabulary": {"ai": 0},
            "matrix": matrix,
            "indexes": ["doc1", "doc2"],
        }
        model = _make_model(fake_model=fake_model)
        with patch.object(model, "preprocess_topic", return_value=["ai"]):
            result = model.get_most_relevant_docs_by_topic_v2("ai", None)
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0], 3)

    def test_limits_results_to_requested_size(self):
        import numpy as np
        from scipy.sparse import csr_matrix

        matrix = csr_matrix(np.array([[1], [3], [2]]))
        fake_model = {
            "vocabulary": {"ai": 0},
            "matrix": matrix,
            "indexes": ["doc1", "doc2", "doc3"],
        }
        model = _make_model(fake_model=fake_model)
        with patch.object(model, "preprocess_topic", return_value=["ai"]):
            result = model.get_most_relevant_docs_by_topic_v2("ai", 1)
        self.assertEqual(len(result), 1)
