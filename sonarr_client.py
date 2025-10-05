import http.client
import urllib.parse
import json
from http.client import HTTPResponse


class SonarrClient:
    BASE_PATH = "/api/v3"

    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}

    def call_endpoint(self, http_method: str, endpoint: str, params=None, json_data=None) -> HTTPResponse:
        if params is None:
            params = {}

        params["apiKey"] = self.api_key

        base = f"{self.base_url}{self.BASE_PATH}{endpoint}"
        parsed_url = urllib.parse.urlparse(base)
        query = urllib.parse.urlencode(params)
        path = parsed_url.path + "?" + query

        if parsed_url.scheme == "https":
            conn = http.client.HTTPSConnection(parsed_url.netloc)
        else:
            conn = http.client.HTTPConnection(parsed_url.netloc)

        body = None
        headers = self.headers if self.headers else {}

        if json_data is not None:
            body = json.dumps(json_data)

        headers['Content-Type'] = 'application/json'

        conn.request(http_method.upper(), path, body=body, headers=headers)
        response = conn.getresponse()

        if 200 <= response.status < 300:
            return response
        else:
            raise Exception(f"API call failed with status: {response.status}, content: {response.read()}")
