import os

from dotenv import load_dotenv

from common.custom_request import CustomRequest

load_dotenv()


class RetrieveScopusData:
    BASE_URL = "https://api.elsevier.com/content/search/scopus"
    HEADERS = {
        "Accept": "application/json",
        "X-ELS-APIKey": os.environ.get("X_ELS_APIKEY"),
        "X-ELS-Insttoken": os.environ.get("X_ELS_INSTTOKEN"),
    }

    def __init__(self):
        self.custom_request = CustomRequest(self.BASE_URL, self.HEADERS)

    def retrieve_data(self) -> dict:
        endpoint = ""
        params = {
            "query": "AFFIL(AFFILCOUNTRY(Ecuador))",
            "count": 25,
            "view": "COMPLETE",
            "field": "dc:identifier,doi,dc:title,coverDate,dc:description,authkeywords,afid,affilname,"
            "affiliation-city,affiliation-country,authid,authname,given-name,surname,initials",
            "cursor": "*",
        }

        try:
            response = self.custom_request.do_get(endpoint, params)
            return response
        except Exception as e:
            print(f"Error: {e}")

    def get_total_articles_from_scopus(self):
        try:
            response = self.retrieve_data()
            return response["search-results"]["opensearch:totalResults"]
        except Exception as e:
            raise Exception(f"Error getting total articles from Scopus: {e}")
