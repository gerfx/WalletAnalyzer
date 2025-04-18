import requests
import time
from typing import List, Dict
from src.config import settings

class BlockchainClient:
    BASE_URL = 'https://api.etherscan.io/api'

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.ETHERSCAN_API_KEY

    def fetch_transactions(self, address: str, start_block: int = 0, end_block: int = 99999999) -> List[Dict]:
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': start_block,
            'endblock': end_block,
            'sort': 'asc',
            'apikey': self.api_key
        }
        response = requests.get(self.BASE_URL, params=params)
        data = response.json()
        if data['status'] != '1':
            raise Exception(f"Error fetching transactions: {data.get('message')}")
        # пауза, чтобы не превысить rate limit
        time.sleep(0.2)
        return data['result']