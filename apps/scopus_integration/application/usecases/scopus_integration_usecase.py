import logging
from urllib.parse import quote_plus as url_encode

from apps.scopus_integration.application.services.scopus_client import ScopusClient
from apps.scopus_integration.domain.repositories.search_affiliations_repository import (
    SearchAffiliationRepository,
)

logger = logging.getLogger("django")


class ScopusIntegrationUseCase:
    def __init__(self, scopus_client: ScopusClient):
        self.scopus_client = scopus_client
        self.search_affiliation_repository = None

    def execute(self, year=None):
        search_type = "scopus"
        view = "COMPLETE"
        field = (
            "dc:identifier,doi,dc:title,coverDate,dc:description,authkeywords,afid,affilname,"
            "affiliation-city,affiliation-country,authid,authname,given-name,surname,initials"
        )
        count = "25"
        cursor = "*"
        query = url_encode("AFFIL(AFFILCOUNTRY(Ecuador))")

        # Un solo año por llamada (en vez del rango fijo 2010-2020 que esto
        # reemplaza) para no traer una decada entera en un solo request: cada
        # llamada es mas chica, mas facil de reintentar si falla, y permite
        # ir acumulando year por year sin bloquear horas en un solo request.
        date_range = str(year) if year else "2010-2020"
        url = f"https://api.elsevier.com/content/search/{search_type}?query={query}&count={count}&view={view}&field={field}&cursor={cursor}&date={date_range}"
        affiliation_repository = SearchAffiliationRepository(url=url)
        self.search_affiliation_repository = affiliation_repository
        print("Iniciando la ejecucion de la busqueda .....")
        logger.log(logging.INFO, "Iniciando la ejecucion de la busqueda .....")
        results = self.search_affiliation_repository.retrieve(
            client=self.scopus_client, get_all=True
        )
        logger.log(logging.INFO, f"Se encontraron {len(results)} resultados")
