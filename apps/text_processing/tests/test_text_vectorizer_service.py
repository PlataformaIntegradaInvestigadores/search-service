"""Unitarias de TextVectorizerService: clean_text, detect_language,
translate_text, generate_embedding y el flujo completo vectorize_text.

El servicio es un singleton por proceso (_instance/_initialized a nivel de
clase), asi que cada test resetea ese estado y mockea SentenceTransformer,
GoogleTranslator y nltk.corpus.stopwords antes de instanciar, para no cargar
el modelo real de 421MB ni pegarle a red (traduccion/deteccion de idioma)."""

from unittest.mock import MagicMock, patch

import numpy as np
from django.test import SimpleTestCase

from apps.text_processing.application.services.text_vectorizer_service import (
    TextVectorizerService,
)

MODULE = "apps.text_processing.application.services.text_vectorizer_service"


class VectorizerTestCase(SimpleTestCase):
    """Resetea el singleton y mockea las dependencias pesadas antes de cada test."""

    def setUp(self):
        TextVectorizerService._instance = None
        TextVectorizerService._initialized = False

        self.st_patcher = patch(f"{MODULE}.SentenceTransformer")
        self.translator_patcher = patch(f"{MODULE}.GoogleTranslator")
        self.stopwords_patcher = patch(f"{MODULE}.stopwords")
        self.langdetect_patcher = patch(f"{MODULE}.langdetect")

        self.mock_st_cls = self.st_patcher.start()
        self.mock_translator_cls = self.translator_patcher.start()
        self.mock_stopwords = self.stopwords_patcher.start()
        self.mock_langdetect = self.langdetect_patcher.start()

        self.mock_model = MagicMock()
        self.mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        self.mock_st_cls.return_value = self.mock_model

        self.mock_translator = MagicMock()
        self.mock_translator.translate.return_value = "translated text"
        self.mock_translator_cls.return_value = self.mock_translator

        def stopwords_words(lang):
            if lang == "spanish":
                return ["el", "la", "de", "que"]
            return ["the", "is", "a"]

        self.mock_stopwords.words.side_effect = stopwords_words

        self.addCleanup(self.st_patcher.stop)
        self.addCleanup(self.translator_patcher.stop)
        self.addCleanup(self.stopwords_patcher.stop)
        self.addCleanup(self.langdetect_patcher.stop)
        self.addCleanup(self._reset_singleton)

    def _reset_singleton(self):
        TextVectorizerService._instance = None
        TextVectorizerService._initialized = False


class TestInitialization(VectorizerTestCase):
    def test_inicializa_modelo_traductor_y_stopwords(self):
        service = TextVectorizerService()

        self.mock_st_cls.assert_called_once_with(service.scibert_model_path)
        self.mock_translator_cls.assert_called_once_with(source="auto", target="en")
        self.assertEqual(service.stop_words, {"the", "is", "a"})

    def test_es_singleton(self):
        service_a = TextVectorizerService()
        service_b = TextVectorizerService()

        self.assertIs(service_a, service_b)
        self.mock_st_cls.assert_called_once()

    def test_error_de_inicializacion_se_propaga(self):
        self.mock_st_cls.side_effect = RuntimeError("no se pudo cargar el modelo")

        with self.assertRaises(RuntimeError):
            TextVectorizerService()


class TestCleanText(VectorizerTestCase):
    def test_remueve_caracteres_especiales_y_normaliza_espacios(self):
        service = TextVectorizerService()

        result = service.clean_text("Hello,   World! ¿Qué tal?")

        self.assertEqual(result, "hello world qué tal")

    def test_colapsa_espacios_multiples(self):
        service = TextVectorizerService()

        self.assertEqual(service.clean_text("a    b\n\nc"), "a b c")


class TestDetectLanguage(VectorizerTestCase):
    def test_detecta_espanol_por_stopwords(self):
        service = TextVectorizerService()

        result = service.detect_language("el gato come")

        self.assertEqual(result, "es")
        self.mock_langdetect.detect.assert_not_called()

    def test_usa_langdetect_si_no_hay_stopwords_espanolas(self):
        service = TextVectorizerService()
        self.mock_langdetect.detect.return_value = "en"

        result = service.detect_language("the cat eats")

        self.assertEqual(result, "en")

    def test_error_retorna_es_por_defecto(self):
        service = TextVectorizerService()
        self.mock_langdetect.detect.side_effect = RuntimeError("boom")

        result = service.detect_language("xyz")

        self.assertEqual(result, "es")


class TestTranslateText(VectorizerTestCase):
    def test_no_traduce_si_ya_esta_en_idioma_destino(self):
        service = TextVectorizerService()
        self.mock_langdetect.detect.return_value = "en"

        text, was_translated, elapsed = service.translate_text("the cat eats", "en")

        self.assertEqual(text, "the cat eats")
        self.assertFalse(was_translated)
        self.assertEqual(elapsed, 0)
        self.mock_translator.translate.assert_not_called()

    def test_traduce_si_idioma_distinto(self):
        service = TextVectorizerService()

        text, was_translated, elapsed = service.translate_text("el gato come", "en")

        self.assertEqual(text, "translated text")
        self.assertTrue(was_translated)
        self.assertGreaterEqual(elapsed, 0)
        self.mock_translator.translate.assert_called_once_with("el gato come")

    def test_error_de_traduccion_retorna_texto_original(self):
        service = TextVectorizerService()
        self.mock_translator.translate.side_effect = RuntimeError("api caida")

        text, was_translated, elapsed = service.translate_text("el gato come", "en")

        self.assertEqual(text, "el gato come")
        self.assertFalse(was_translated)
        self.assertEqual(elapsed, 0)


class TestGenerateEmbedding(VectorizerTestCase):
    def test_genera_embedding_desde_el_modelo(self):
        service = TextVectorizerService()

        result = service.generate_embedding("texto de prueba")

        self.mock_model.encode.assert_called_once_with(
            "texto de prueba", convert_to_tensor=False
        )
        np.testing.assert_array_equal(result, np.array([0.1, 0.2, 0.3]))

    def test_error_al_generar_embedding_se_propaga(self):
        service = TextVectorizerService()
        self.mock_model.encode.side_effect = RuntimeError("modelo caido")

        with self.assertRaises(RuntimeError):
            service.generate_embedding("texto")


class TestVectorizeText(VectorizerTestCase):
    def test_flujo_completo_con_traduccion_y_limpieza(self):
        service = TextVectorizerService()

        result = service.vectorize_text("el gato, come!")

        self.assertEqual(result["original_language"], "es")
        self.assertTrue(result["was_translated"])
        self.assertEqual(result["processed_text"], "translated text")
        self.assertEqual(result["dimension"], 3)
        self.assertEqual(result["vector"], [0.1, 0.2, 0.3])
        self.assertIn("total_time", result["processing_time"])

    def test_sin_traduccion_ni_limpieza(self):
        service = TextVectorizerService()
        self.mock_langdetect.detect.return_value = "en"

        result = service.vectorize_text(
            "The Cat, Eats!", translate_to_english=False, clean_text=False
        )

        self.assertFalse(result["was_translated"])
        self.assertEqual(result["processed_text"], "The Cat, Eats!")

    def test_no_traduce_si_ya_es_ingles(self):
        service = TextVectorizerService()
        self.mock_langdetect.detect.return_value = "en"

        result = service.vectorize_text("the cat eats")

        self.assertFalse(result["was_translated"])
        self.mock_translator.translate.assert_not_called()

    def test_error_en_embedding_se_propaga(self):
        service = TextVectorizerService()
        self.mock_model.encode.side_effect = RuntimeError("modelo caido")

        with self.assertRaises(RuntimeError):
            service.vectorize_text("el gato come")
