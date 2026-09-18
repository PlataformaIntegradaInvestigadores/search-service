from typing import Any

import requests


class CustomRequest:

    def __init__(self, base_url: str, headers: dict = None):
        self.base_url = base_url
        self.headers = headers

    def do_get(self, endpoint: str, params: dict) -> Any:
        try:
            url = self.base_url + endpoint
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error on do get: {e}")

    def do_post(self, endpoint: str, data: dict) -> Any:
        try:
            url = self.base_url + endpoint
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error on do post: {e}")
