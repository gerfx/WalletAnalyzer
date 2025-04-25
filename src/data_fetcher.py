import requests
from requests.adapters import HTTPAdapter, Retry

class EtherscanClient:
    BASE_URL = "https://api.etherscan.io/api"

    def __init__(self, api_key, timeout=10):
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[500,502,503,504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def _get(self, params):
        params.update({"apikey": self.api_key})
        resp = self.session.get(self.BASE_URL, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        if data.get('status') != '1':
            raise RuntimeError(data.get('message', 'Unknown error from Etherscan'))
        return data['result']

    def fetch_normal_transactions(self, address, startblock=0, endblock=99999999, sort='asc'):
        """Получает список обычных транзакций."""
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": startblock,
            "endblock": endblock,
            "sort": sort
        }
        return self._get(params)

    def fetch_token_transfers(self, address, startblock=0, endblock=99999999, sort='asc'):
        """Получает список ERC-20 трансферов."""
        params = {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "startblock": startblock,
            "endblock": endblock,
            "sort": sort
        }
        return self._get(params)
