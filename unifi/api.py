import requests
import logging
import json
import os

logger = logging.getLogger(__name__)


class UnifiError(Exception):
    pass


class UnifiApiError(UnifiError):
    def __init__(self, response):
        self.response = response
        try:
            error_msg = response.json()["meta"]["msg"]
        except KeyError:
            error_msg = response.text
        super().__init__(f"API Error: {error_msg}")


class UnifiClient:
    def __init__(self, endpoint, username, password, verify_ssl=True):
        self.endpoint = endpoint
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.verify = verify_ssl

    def _request(self, method, path, **kwargs):
        url = f"{self.endpoint}/api/s/default/{path}"
        print(url)
        response = self.session.request(method, url, **kwargs)
        if not response.ok:
            raise UnifiApiError(response)
        return response.json()

    def get(self, path, **kwargs):
        return self._request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self._request("POST", path, **kwargs)

    def put(self,path, **kwargs):
        return self._request("PUT", path, **kwargs)

    def delete(self, path, **kwargs):
        return self._request("DELETE", path, **kwargs)


# if __name__ == "__main__":
#     endpoint, username, password, verify_ssl = get_controller_credentials()
#     controller = UnifiClient(endpoint, username, password, verify_ssl)

#     # Example usage (get all devices):
#     devices = controller.get("stat/device")["data"]
#     for device in devices:
#         print(device["name"], device["ip"], device["type"])
