def display_features(features: dict):
    """Печатает наглядный отчёт по признакам."""
    lines = [
        "Анализ активности кошелька:",
        "--------------------------",
        f"Общее количество транзакций: {features['total_transactions']}",
        f"Уникальные контракты:          {features['unique_contracts']}",
        f"Уникальные токены:            {features['unique_tokens']}",
        f"Возраст кошелька (дн):        {features['wallet_age_days']:.1f}",
        f"Частота (транз./дн):          {features['transaction_frequency']:.2f}",
        f"Среднее межтранзакц. (ч):     {features['avg_time_between_txs']:.2f}",
        f"Макс транзакций в день:       {features['max_txs_per_day']}",
        f"Уникальных отправителей:      {features['unique_funders']}",
        f"Исходящих ETH-транзакций:     {features['outgoing_eth_txs']}",
        f"Сред. исходящий ETH:          {features['avg_outgoing_eth_value']:.4f} ETH",
        f"СКО исходящего ETH:           {features['std_outgoing_eth_value']:.4f} ETH",
        f"Уникальных получателей:       {features['unique_recipients']}"
    ]
    report = "\n".join(lines)
    print(report)

    # Эвристика
    if (features['transaction_frequency'] > 10 and 
        features['wallet_age_days'] < 30 and 
        features['unique_contracts'] < 5):
        print("\n[!] Внимание: кошелек может быть сибильным.")
    elif (features['transaction_frequency'] < 0.1 and 
          features['wallet_age_days'] > 365 and 
          features['unique_contracts'] > 50):
        print("\n[!] Внимание: кошелек может быть заброшен.")
    elif (features['avg_outgoing_eth_value'] > 10 and 
          features['outgoing_eth_txs'] > 5):
        print("\n[!] Внимание: кошелек может быть связан с крупными транзакциями.")
    elif (features['unique_tokens'] > 20 and 
          features['transaction_frequency'] > 1):
        print("\n[!] Внимание: кошелек может быть связан с активной торговлей токенами.")
    else:
        print("\n[!] Кошелек выглядит нормальным.")
