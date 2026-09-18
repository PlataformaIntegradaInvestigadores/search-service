import os


class ModelCorpusObserverService:
    def __init__(self):
        self.corpus_path = None
        self.model_path = None
        self.build_model_path()
        self.build_corpus_path()

    def build_corpus_path(self):
        try:
            modelo = "tf-idf"
            base_path = "resources/corpus/"
            version = "v10.0"
            corpus_path = base_path + "corpus-" + modelo + "-" + version + ".pkl"
            self.corpus_path = corpus_path
        except Exception as e:
            raise Exception("Error building model path: " + str(e))

    def build_model_path(self):
        try:
            base_path = "resources/models/tf-idf/"
            version = "v10.0"
            model_path = base_path + "model-" + version + ".pkl"
            self.model_path = model_path
        except Exception as e:
            raise Exception("Error building corpus path: " + str(e))

    def verify_corpus_path_exists(self) -> bool:
        try:
            return os.path.exists(self.corpus_path)
        except Exception as e:
            raise Exception("Error verifying model path exists: " + str(e))

    def verify_model_path_exists(self) -> bool:
        try:
            return os.path.exists(self.model_path)
        except Exception as e:
            raise Exception("Error verifying corpus path exists: " + str(e))

    def delete_corpus(self) -> bool:
        try:
            if not self.verify_corpus_path_exists():
                return True
            os.remove(self.corpus_path)
            return True
        except Exception as e:
            raise Exception("Error deleting corpus: " + str(e))

    def delete_model(self) -> bool:
        try:
            if not self.verify_model_path_exists():
                return True
            os.remove(self.model_path)
            return True
        except Exception as e:
            raise Exception("Error deleting model: " + str(e))
