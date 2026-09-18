import pickle
from string import punctuation

import nltk
import pandas as pd
import spacy
from deep_translator import GoogleTranslator
from keybert import KeyBERT
from langdetect import detect
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from unidecode import unidecode

nltk.download("stopwords")


class Model:
    tokenizer = TfidfVectorizer().build_tokenizer()
    stop_words = [unidecode(stopW) for stopW in stopwords.words("english")]
    non_words = list(punctuation) + ["¿", "¡", "...", ".."]
    stop_words += non_words

    _nlp = None
    _kw_model = None

    @classmethod
    def get_nlp(cls):
        if cls._nlp is None:
            cls._nlp = spacy.load("en_core_web_sm")
        return cls._nlp

    @classmethod
    def get_kw_model(cls):
        if cls._kw_model is None:
            cls._kw_model = KeyBERT()
        return cls._kw_model

    def __init__(self, type):
        self.type = type
        self.base_path = "resources/"
        self.model = self.load_model(type)
        self.nlp = self.get_nlp()
        self.kw_model = self.get_kw_model()
        self.translator = GoogleTranslator(source="auto", target="en")

    def load_model(self, model_type: str):
        try:
            if not isinstance(model_type, str):
                raise ValueError("Type must be a string")

            root = self.base_path
            path = (
                root + "models/tf-idf/model-v10.0.pkl"
                if model_type in ["author", "article"]
                else root + "models/model-v11.0.pkl"
            )

            with open(path, "rb") as fp:
                return pickle.load(fp)

        except Exception as e:
            raise Exception(f"Error while loading model: {str(e)}")

    def detect_language(self, text):
        try:
            return detect(text)
        except:
            return "es"

    def clean_text(self, text):
        text = unidecode(text.lower())
        return "".join(
            [char if char.isalnum() or char.isspace() else " " for char in text]
        ).strip()

    def enhance_query_semantically(self, query):
        if len(query.split()) <= 3:
            return query

        keywords = self.kw_model.extract_keywords(
            query, keyphrase_ngram_range=(1, 2), stop_words="english", top_n=5
        )
        doc = self.nlp(query)
        important_words = [
            token.text
            for token in doc
            if token.is_alpha and token.text.lower() not in self.stop_words
        ]
        enhanced_query = " ".join(set(important_words + [kw[0] for kw in keywords]))
        return enhanced_query

    def process_query(self, query):
        lang = self.detect_language(query)
        if lang != "en":
            query = self.translator.translate(query)
        cleaned_query = self.clean_text(query)
        enhanced_query = self.enhance_query_semantically(cleaned_query)
        return enhanced_query

    def preprocess_topic(self, topic):
        topic = self.process_query(topic)
        tokens = self.tokenizer(topic)
        return [
            word for word in tokens if word not in self.stop_words and len(word) > 2
        ]

    def get_most_relevant_docs_by_topic_v2(self, topic, author_size):
        preprocessed_topic = self.preprocess_topic(topic)
        valid_tokens = [
            token for token in preprocessed_topic if token in self.model["vocabulary"]
        ]

        if not valid_tokens:
            return pd.Series()

        token_ids = [self.model["vocabulary"][token] for token in valid_tokens]
        data = {
            tokenId: [
                item[0]
                for item in self.model["matrix"]
                .getcol(tokenId)
                .sorted_indices()
                .toarray()
            ]
            for tokenId in token_ids
        }
        df_result = pd.DataFrame(data=data, index=self.model["indexes"])

        scores = df_result.sum(axis=1) / len(valid_tokens)
        return (
            scores.sort_values(ascending=False).head(author_size)
            if author_size
            else scores.sort_values(ascending=False)
        )
