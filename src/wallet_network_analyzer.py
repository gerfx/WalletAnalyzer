import argparse
import json
import logging
import yaml
import time
import os
from collections import deque
from data_fetcher import EtherscanClient
from feature_extractor import calculate_features
from utils import validate_address


def load_config(path="config/config.yaml"):
    with open(path) as f:
        cfg = yaml.safe_load(f)
    try:
        return cfg['etherscan_api_key']
    except KeyError:
        raise KeyError("Config missing 'etherscan_api_key'")


def get_related_wallets(normal_txs: list[dict], token_txs: list[dict], address: str) -> set[str]:
    address = address.lower()
    related_wallets = set()

    for tx in normal_txs:
        if tx['from'].lower() == address and tx['to'].lower() != address:
            related_wallets.add(tx['to'].lower())
        elif tx['to'].lower() == address and tx['from'].lower() != address:
            related_wallets.add(tx['from'].lower())

    for tx in token_txs:
        if tx['from'].lower() == address and tx['to'].lower() != address:
            related_wallets.add(tx['to'].lower())
        elif tx['to'].lower() == address and tx['from'].lower() != address:
            related_wallets.add(tx['from'].lower())
    
    return {w for w in related_wallets if len(w) == 42}


def analyze_wallet_network(initial_address: str, max_wallets: int = 100, api_key: str = None) -> dict[str, dict]:
    client = EtherscanClient(api_key)
    wallet_features = {}
    processed_wallets = set()
    wallet_queue = deque([initial_address])
    
    while wallet_queue and len(processed_wallets) < max_wallets:
        current_address = wallet_queue.popleft()
        
        if current_address.lower() in processed_wallets:
            continue
            
        try:
            logging.info(f"Analyzing wallet: {current_address} ({len(processed_wallets) + 1}/{max_wallets})")
            
            normal_txs = client.fetch_normal_transactions(current_address)
            token_txs = client.fetch_token_transfers(current_address)
            
            features = calculate_features(normal_txs, token_txs, current_address)
            wallet_features[current_address] = features
            processed_wallets.add(current_address.lower())
            
            related_wallets = get_related_wallets(normal_txs, token_txs, current_address)
            
            # Add new wallets to the queue
            for wallet in related_wallets:
                if wallet.lower() not in processed_wallets:
                    try:
                        validated_address = validate_address(wallet)
                        wallet_queue.append(validated_address)
                    except ValueError:
                        logging.warning(f"Invalid address format: {wallet}")
            
            time.sleep(0.5)
            
        except Exception as e:
            logging.error(f"Error processing wallet {current_address}: {e}")
            processed_wallets.add(current_address.lower())
    
    return wallet_features


def main():
    parser = argparse.ArgumentParser(description="Recursively analyze Ethereum wallet network")
    parser.add_argument("address", help="Initial wallet address")
    parser.add_argument("--max-wallets", type=int, default=100, help="Maximum number of wallets to analyze")
    parser.add_argument("--output", default="wallet_network.json", help="Output JSON file path")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    try:
        api_key = load_config(args.config)
        address = validate_address(args.address)
    except Exception as e:
        logging.error(f"Configuration error: {e}")
        return

    try:
        logging.info(f"Starting recursive wallet analysis from {address} with max {args.max_wallets} wallets")
        wallet_features = analyze_wallet_network(address, args.max_wallets, api_key)
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(wallet_features, f, indent=2)
        
        logging.info(f"Analysis complete. Processed {len(wallet_features)} wallets.")
        logging.info(f"Results saved to {os.path.abspath(args.output)}")
        
    except Exception as e:
        logging.error(f"Error during analysis: {e}")


if __name__ == "__main__":
    main()
