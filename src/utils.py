from eth_utils import is_address, to_checksum_address

def validate_address(address: str) -> str:
    """Проверяет и возвращает адрес в формате checksum."""
    if not isinstance(address, str) or not is_address(address):
        raise ValueError(f"Неверный формат Ethereum-адреса: {address}")
    return to_checksum_address(address)
