from typing import Dict, Optional

from binance.client import Client


def get_exchange_info_for_symbol(client: Client, symbol: str) -> Optional[Dict]:
    """Get exchange info for a given symbol (e.g. "DOGEUSDT")

    You need to give it a client (binance.client.Client), initialized w/ the pkey and skey
    """
    exchange_info = client.get_exchange_info()
    for symbol_data in exchange_info["symbols"]:
        if symbol_data["symbol"] == symbol:
            return symbol_data
    return None


def passes_filters(client: Client, symbol: str, price: float, quantity: float):
    exchange_info = get_exchange_info_for_symbol(client, symbol)

    precision = exchange_info["baseAssetPrecision"]

    for flt in exchange_info["filters"]:
        print(flt)


def pass_price_filter(filter_conditions: Dict, price: float) -> bool:
    within_price_range = (
        filter_conditions["minPrice"] <= price <= filter_conditions["maxPrice"]
    )
    price_mod_ticksize = (price - minPrice) % filter_conditions["tickSize"] == 0
    return within_price_range and price_mod_ticksize
