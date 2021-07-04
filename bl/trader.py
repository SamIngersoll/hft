from typing import Optional, Dict

from order_side import OrderSide
from ema_strategy import EMA_strategy

from binance import helpers
from binance.client import Client


"""
This is all certainly unrefined - difficult to read, over complex, wall of text, etc.
there are also certainly some nice abstractions that can be leveraged to make things
tidy.
"""


class Trader:
    def __init__(
        self,
        symbol: str,
        client: Client,
        optimization_period: int = 1500,
        async_optimization: bool = False,
        verbose: bool = False,
    ):
        self.symbol = symbol
        self.client = client
        self.optimization_period = optimization_period
        self.async_optimization = async_optimization
        self.verbose = verbose

        self._optimize_async_result = None
        self.price_history = []
        self.base_quantity = 0
        self.quote_quantity = 0
        self.num_buys = 0
        self.num_sells = 0

        self.strategy = EMA_strategy()
        self.symbol_info = self.get_symbol_info(client, symbol)  # network call
        self._update_symbol_quantities()  # another network call

    def _update_symbol_quantities(self):
        self.base_quantity = float(
            self.client.get_asset_balance(asset=self.symbol_info["baseAsset"])["free"]
        )
        self.quote_quantity = float(
            self.client.get_asset_balance(asset=self.symbol_info["quoteAsset"])["free"]
        )

    def _get_filters(self) -> Dict[str, Dict]:
        d = dict()
        for filt in self.symbol_info["filters"]:
            d[filt["filterType"]] = filt
        return d

    def get_symbol_info(self, client: Client, symbol: str) -> Dict[str, str]:
        exchange_info = client.get_exchange_info()
        for symbol_data in exchange_info["symbols"]:
            if symbol_data["symbol"] == self.symbol:
                return symbol_data
        raise RuntimeError(f"could not find symbol {symbol} in exchange data")

    def trade(self, price):
        self.price_history.append(price)
        if len(self.price_history) < self.optimization_period:
            return OrderSide.NO_OP
        elif len(self.price_history) == self.optimization_period:
            if self.async_optimization:
                self.optimize_async_result = self.strategy.optimize_multiprocess_async(
                    self.price_history, ema_const_range=10
                )
            else:
                self.strategy.optimize_multiprocess(
                    self.price_history, ema_const_range=10
                )
            return OrderSide.NO_OP
        elif self.async_optimization:
            if not self.optimize_async_result.ready():
                return OrderSide.NO_OP

        traded = False
        action = self.strategy.action(price)
        if action == OrderSide.BUY:  # buy
            if self.base_quantity > 0:
                self.build_limit_buy(price)
                traded = True
        elif action == OrderSide.SELL:  # sell
            if self.quote_quantity > 0:
                self.build_limit_sell(price)
                traded = True

        if len(self.price_history) % self.optimization_period == 0:
            if self.async_optimization:
                self.strategy.optimize_multiprocess_async(
                    self.price_history[-self.optimization_period : -1],
                    ema_const_range=10,
                )
            else:
                self.strategy.optimize_multiprocess(
                    self.price_history[-self.optimization_period : -1],
                    ema_const_range=10,
                )

        if traded:
            self._update_symbol_quantities()
            return action
        return OrderSide.NO_OP

    def format_filters(self, price) -> Dict:
        """ not done yet """
        filters = self._get_filters()

        # assuming base precision == quote precision
        precision = int(self.symbol_info["baseAssetPrecision"])
        price_value = helpers.round_step_size(
            price, float(filters["PRICE_FILTER"]["tickSize"])
        )
        quantity = helpers.round_step_size(
            self.base_quantity, float(filters["LOT_SIZE"]["stepSize"])
        )

        min_price = float(filters["PRICE_FILTER"]["minPrice"])
        max_price = float(filters["PRICE_FILTER"]["maxPrice"])
        min_qty = float(filters["LOT_SIZE"]["minQty"])
        max_qty = float(filters["LOT_SIZE"]["maxQty"])
        assert min_price <= price <= max_price
        assert min_qty <= quantity <= max_qty

        return {
            "min_notional_value": filters["MIN_NOTIONAL"]["minNotional"],
            "quantity": f"{quantity:.{precision}f}",
            "price": f"{price_value:.{precision}f}",
        }

    def build_limit_buy(self, price: float):
        order_values = self.format_filters(price)
        self.client.order_limit_buy(
            symbol=self.symbol,
            quantity=order_values["quantity"],
            price=order_values["price"],
        )

    def build_limit_sell(self, price: float):
        order_values = self.format_filters(price)
        self.client.order_limit_sell(
            symbol=self.symbol,
            quantity=order_values["quantity"],
            price=order_values["price"],
        )
