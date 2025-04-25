from datetime import datetime
from collections import defaultdict
import statistics
import time

def calculate_features(normal_txs, token_txs, wallet_address):
    wallet = wallet_address.lower()
    all_txs = []

    # Приведение timestamp к int и запись транзакции
    for tx in normal_txs + token_txs:
        tx['timeStamp'] = int(tx['timeStamp'])
        all_txs.append(tx)
    all_txs.sort(key=lambda x: x['timeStamp'])

    features = {}
    features['total_transactions'] = len(all_txs)

    # Исходящие обычные
    outgoing = [tx for tx in normal_txs if tx['from'].lower() == wallet]
    incoming = [tx for tx in normal_txs if tx['to'].lower() == wallet]

    features['unique_contracts'] = len({tx['to'].lower() for tx in outgoing})
    features['unique_tokens']    = len({tx['contractAddress'].lower() for tx in token_txs})
    
    if all_txs:
        first_ts = all_txs[0]['timeStamp']
        last_ts  = all_txs[-1]['timeStamp']
        now_ts   = int(time.time())
        features['wallet_age_days'] = (now_ts - first_ts) / 86400
        active_days = max((last_ts - first_ts) / 86400, 1e-6)
        features['transaction_frequency'] = len(all_txs) / active_days
    else:
        features['wallet_age_days'] = 0
        features['transaction_frequency'] = 0

    # Среднее время между транзакциями
    intervals = [
        all_txs[i+1]['timeStamp'] - all_txs[i]['timeStamp']
        for i in range(len(all_txs)-1)
    ]
    features['avg_time_between_txs'] = (statistics.mean(intervals) / 3600) if intervals else 0

    # Максимум транзакций в день
    count_per_day = defaultdict(int)
    for tx in all_txs:
        date = datetime.utcfromtimestamp(tx['timeStamp']).date()
        count_per_day[date] += 1
    features['max_txs_per_day'] = max(count_per_day.values(), default=0)

    features['unique_funders']      = len({tx['from'].lower() for tx in incoming})
    features['outgoing_eth_txs']    = len(outgoing)

    # Среднее и СКО исходящих ETH
    eth_values = [
        int(tx.get('value', 0)) / 1e18
        for tx in outgoing if int(tx.get('value', 0)) > 0
    ]
    if eth_values:
        features['avg_outgoing_eth_value'] = statistics.mean(eth_values)
        features['std_outgoing_eth_value'] = statistics.stdev(eth_values) if len(eth_values) > 1 else 0
    else:
        features['avg_outgoing_eth_value'] = 0
        features['std_outgoing_eth_value'] = 0

    features['unique_recipients'] = len({tx['to'].lower() for tx in outgoing})
    return features
