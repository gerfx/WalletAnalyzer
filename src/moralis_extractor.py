import requests
from requests.adapters import HTTPAdapter, Retry

class MoralisClient:
    BASE_URL = "https://deep-index.moralis.io/api/v2"

    def __init__(self, api_key, timeout=10):
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[500,502,503,504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.headers = {
            "accept": "application/json",
            "X-API-Key": self.api_key
        }

    def _get(self, endpoint, params=None):
        url = f"{self.BASE_URL}/{endpoint}"
        resp = self.session.get(url, headers=self.headers, params=params or {}, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return data

    def fetch_normal_transactions(self, address, chain='eth'):
        endpoint = f"{address}"
        params = {
            "chain": chain
        }
        data = self._get(endpoint, params)
        return data.get('result', [])

    def fetch_token_transfers(self, address, chain='eth'):
        endpoint = f"{address}/erc20/transfers"
        params = {
            "chain": chain
        }
        data = self._get(endpoint, params)
        return data.get('result', [])
