import logging
import os
import re
import time

import langdetect
import numpy as np
from deep_translator import GoogleTranslator
from nltk.corpus import stopwords
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class TextVectorizerService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            BASE_DIR = "resources/"
            self.scibert_model_path = os.path.join(
                BASE_DIR, "models", "scibert_scivocab_uncased"
            )
            self.initialize_components()
            self.__class__._initialized = True

    def initialize_components(self):
        """Initialize models and components for text processing"""
        try:
            # Load SentenceTransformer model for embeddings
            self.scibert_model = SentenceTransformer(self.scibert_model_path)

            # Initialize translator
            self.translator = GoogleTranslator(source="auto", target="en")

            # Load stopwords
            self.stop_words = set(stopwords.words("english"))

            logger.info("Text vectorizer components initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing text vectorizer components: {e}")
            raise

    def detect_language(self, text: str) -> str:
        """Detect the language of input text"""
        try:
            text_lower = text.lower()
            words = text_lower.split()
            spanish_stopwords = set(stopwords.words("spanish"))

            # Check for Spanish words first
            if any(word in spanish_stopwords for word in words):
                logger.info("Spanish word(s) detected, treating as Spanish")
                return "es"

            # Use langdetect for other languages
            lang = langdetect.detect(text)
            logger.info(f"Detected language: {lang}")
            return lang

        except Exception as e:
            logger.warning(f"Language detection error: {e}. Using 'es' as default")
            return "es"

    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove special characters except spaces
        text = re.sub(r"[^\w\s]", " ", text)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip().lower()

    def translate_text(
        self, text: str, target_lang: str = "en"
    ) -> tuple[str, bool, float]:
        """Translate text to target language if needed"""
        translation_time = 0
        was_translated = False

        try:
            detected_lang = self.detect_language(text)

            if detected_lang != target_lang:
                translation_start = time.time()
                translated_text = self.translator.translate(text)
                translation_time = time.time() - translation_start
                was_translated = True
                logger.info(f"Translated from {detected_lang} to {target_lang}")
                return translated_text, was_translated, translation_time
            else:
                return text, was_translated, translation_time

        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text, was_translated, translation_time

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding vector for text using SciBERT"""
        try:
            # Generate embedding using SentenceTransformer
            embedding = self.scibert_model.encode(text, convert_to_tensor=False)
            return embedding

        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            raise

    def vectorize_text(
        self, text: str, translate_to_english: bool = True, clean_text: bool = True
    ) -> dict:
        """
        Main method to vectorize text with preprocessing

        Args:
            text: Input text to vectorize
            translate_to_english: Whether to translate to English
            clean_text: Whether to clean and normalize text

        Returns:
            Dict containing vector, metadata, and processing info
        """
        try:
            logger.info("Starting text vectorization")
            logger.info(f"Original text: '{text[:100]}...'")

            original_language = self.detect_language(text)
            processed_text = text
            was_translated = False
            translation_time = 0

            # Translation step
            if translate_to_english and original_language != "en":
                processed_text, was_translated, translation_time = self.translate_text(
                    processed_text, "en"
                )

            # Cleaning step
            if clean_text:
                processed_text = self.clean_text(processed_text)

            # Generate embedding
            start_time = time.time()
            vector = self.generate_embedding(processed_text)
            embedding_time = time.time() - start_time

            # Prepare response
            result = {
                "vector": vector.tolist(),  # Convert to list for JSON serialization
                "dimension": len(vector),
                "original_language": original_language,
                "was_translated": was_translated,
                "processed_text": processed_text,
                "processing_time": {
                    "translation_time": translation_time,
                    "embedding_time": embedding_time,
                    "total_time": translation_time + embedding_time,
                },
            }

            logger.info(
                f"Text vectorization completed. Vector dimension: {len(vector)}"
            )
            return result

        except Exception as e:
            logger.error(f"Text vectorization error: {e}")
            raise
