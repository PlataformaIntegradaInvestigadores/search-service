import pickle

from sklearn.feature_extraction.text import TfidfVectorizer


class ModelGenerationService:
    @staticmethod
    def read_path():
        try:
            modelo = "tf-idf"
            base_path = "resources/corpus/"
            version = "v10.0"
            corpus_path = base_path + "corpus-" + modelo + "-" + version + ".pkl"
            with open(corpus_path, "rb") as fp:
                corpus = pickle.load(fp)
                return corpus
        except Exception as e:
            raise Exception("Error reading path: " + str(e))

    @staticmethod
    def save_model(model):
        try:
            base_path = "resources/models/tf-idf/"
            version = "v10.0"
            model_path = base_path + "model-" + version + ".pkl"
            with open(model_path, "wb") as fp:
                pickle.dump(model, fp)
        except Exception as e:
            raise Exception("Error saving model: " + str(e))

    def generate_model(self, corpus):
        try:
            tfidf = TfidfVectorizer(norm="l2", smooth_idf=True, sublinear_tf=True)
            matrix = tfidf.fit_transform(corpus["preprocessed_doc"].to_list())
            len(tfidf.get_feature_names_out())
            model = {
                "vocabulary": tfidf.vocabulary_,
                "matrix": matrix,
                "indexes": corpus["doc_id"].to_list(),
            }
            self.save_model(model)
        except Exception as e:
            raise Exception("Error generating model: " + str(e))
