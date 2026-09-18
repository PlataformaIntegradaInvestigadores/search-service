from apps.scopus_integration.application.services.corpus_generation_service import (
    CorpusService,
)


class GenerateCorpusUseCase:
    def __init__(self, corpus_service: CorpusService):
        self.corpus_service = corpus_service

    def execute(self):
        try:
            combined_corpus = self.corpus_service.get_combined_corpus()
            return combined_corpus
        except Exception as e:
            raise Exception("Error while generating corpus ", str(e))
