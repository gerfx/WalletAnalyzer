import argparse
import logging
import yaml
from data_fetcher import EtherscanClient
from feature_extractor import calculate_features
from presenter import display_features
from utils import validate_address

def load_config(path="config/config.yaml"):
    with open(path) as f:
        cfg = yaml.safe_load(f)
    try:
        return cfg['etherscan_api_key']
    except KeyError:
        raise KeyError("В конфиге отсутствует 'etherscan_api_key'")

def main():
    parser = argparse.ArgumentParser(description="Анализ активности Ethereum-кошелька")
    parser.add_argument("address", help="Адрес кошелька")
    parser.add_argument("--config", default="config/config.yaml", help="Путь к файлу конфигурации")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        api_key = load_config(args.config)
        address = validate_address(args.address)
    except Exception as e:
        logging.error(e)
        return

    client = EtherscanClient(api_key)
    try:
        logging.info("Сбор обычных транзакций...")
        normal = client.fetch_normal_transactions(address)
        logging.info("Сбор переводов токенов...")
        tokens = client.fetch_token_transfers(address)
    except Exception as e:
        logging.error(f"Ошибка при сборе данных: {e}")
        return

    features = calculate_features(normal, tokens, address)
    display_features(features)

if __name__ == "__main__":
    main()
