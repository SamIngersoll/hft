from typing import Dict, Optional

from binance.client import Client


def get_exchange_info_for_symbol(client: Client, symbol: str) -> Optional[Dict]:
    """ Get exchange info for a given symbol (e.g. "DOGEUSDT")

    You need to give it a client (binance.client.Client), initialized w/ the pkey and skey
    """
    exchange_info = client.get_exchange_info()
    for symbol_data in exchange_info["symbols"]:
        if symbol_data["symbol"] == symbol:
            return symbol_data
    return None
