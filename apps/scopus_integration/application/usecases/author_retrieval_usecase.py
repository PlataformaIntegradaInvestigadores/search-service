from apps.scopus_integration.application.services.scopus_client import ScopusClient


class AuthorRetrieval:
    """Una author en Scopus."""

    # variables estáticas
    _url_base = "https://api.elsevier.com/content/author/author_id/"

    def __init__(
        self, url=None, response_list=False, author_id=None, view=None, field=None
    ):
        """Inicializa un author dado la URL
        del author o author ID."""
        self.result = None
        self.response_list = response_list

        if url and not author_id:
            self.url = url
        elif author_id and not url:
            self.url = self._url_base + author_id
            params = []
            if view:
                params.append("view=" + view)
            if field:
                params.append("field=" + field)
            if params:
                self.url = self.url + "?" + "&".join(params)
        elif not url and not author_id:
            raise ValueError("You must specify either the URL or the ID.")
        else:
            raise ValueError("You must specify either the URL or the ID, not both.")

    def retrieve(self, client: ScopusClient = None):
        api_response = client.exec_request(self.url)
        if self.response_list:
            self.result = api_response["author-retrieval-response-list"][
                "author-retrieval-response"
            ]
        else:
            self.result = api_response["author-retrieval-response"]
        # TODO filtrar respuesta
