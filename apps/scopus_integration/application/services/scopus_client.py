import json
import os
import time

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3 import Retry

# Load environment variables

load_dotenv()


class ScopusClient:
    __min_req_interval = 1
    __ts_last_req = 0
    _status_code = 0

    def __init__(self):
        self._status_msg = ""
        self.x_els_api_key = os.environ.get("X_ELS_APIKEY")
        self.x_els_ins_token = os.environ.get("X_ELS_INSTTOKEN")
        self.x_els_auth_token = os.environ.get("X_ELS_AUTHTOKEN")

    def exec_request(self, url: str):
        try:
            interval = time.time() - self.__ts_last_req
            if interval < self.__min_req_interval:
                time.sleep(self.__min_req_interval - interval)

            headers = {"X-ELS-APIKey": self.x_els_api_key, "Accept": "application/json"}

            if self.x_els_auth_token:
                headers["X-ELS-Authtoken"] = self.x_els_auth_token
            if self.x_els_ins_token:
                headers["X-ELS-Insttoken"] = self.x_els_ins_token

            session = requests.Session()
            retry = Retry(connect=10, backoff_factor=0.5)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

            r = session.get(url, headers=headers)
            self.__ts_last_req = time.time()
            self._status_code = r.status_code
            if r.status_code == 200:
                self._status_msg = "Data fetched successfully."
                return json.loads(r.text)
            else:
                error_message = f"HTTP {r.status_code}: {r.text}"
                self._status_msg = error_message
                # load error message to json
                json_error = json.loads(r.text)
                raise requests.HTTPError(json_error, response=r)
        except requests.HTTPError as e:
            raise e
        except Exception as e:
            raise Exception(f"Error executing request: {e}")
