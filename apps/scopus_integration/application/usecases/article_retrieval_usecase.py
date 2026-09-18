from apps.scopus_integration.application.services.scopus_client import ScopusClient


class ArticleRetrieval:
    """Un Article en Scopus."""

    # variables estáticas
    _url_base = "https://api.elsevier.com/content/abstract/scopus_id/"

    def __init__(self, url=None, scopus_id=None, view="FULL", field=None):
        """Inicializa un article dado la URL
        del article o Scopus ID."""

        self.result = None
        if url and not scopus_id:
            self.url = url
        elif scopus_id and not url:
            self.url = self._url_base + str(scopus_id)
            if view:
                self.url = self.url + "?view=" + view
            if field:
                self.url = self.url + "&field=" + field
        elif not url and not scopus_id:
            raise ValueError("URL or ID is needed.")
        else:
            raise ValueError("Url or ID is needed, not both.")

    def execute(self, client: ScopusClient = None):
        print("Ejecutando la busqueda de articulos .....")
        print("URL:", self.url)
        api_response = client.exec_request(self.url)
        self.result = api_response["abstracts-retrieval-response"]
        return self.result
