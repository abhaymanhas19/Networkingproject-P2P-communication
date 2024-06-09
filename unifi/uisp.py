import requests
import json

class UcrmApiAccess:
    API_URL = 'https://unms.ui.com/api/v1.0'
    APP_KEY = '4c0ce93b-a9bd-4014-9738-3acf0ac0a253'

    @staticmethod
    def do_request(url, method='GET', post=None):
        method = method.upper()
        headers = {
            'Content-Type': 'application/json',
            'X-Auth-App-Key': UcrmApiAccess.APP_KEY
        }

        full_url = f"{UcrmApiAccess.API_URL}/{url}"
        response = requests.request(method, full_url, headers=headers, json=post)

        if response.status_code >= 400:
            print(f"API error: {response.text}")
            return None

        return response.json()
