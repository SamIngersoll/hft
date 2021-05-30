from order_side import OrderSide
from ema_strategy import EMA_strategy


class Trader:
    def __init__(self, optimization_period=5000, async_optimization=False):
        self.base_arr = []
        self.quote_arr = []
        self.price_history = []
        self.base = 1
        self.quote = 0
        self.tr = EMA_strategy()
        self.optimization_period = optimization_period
        self.optimize_async_result = None
        self.num_buys = 0
        self.num_sells = 0
        self.async_optimization = async_optimization

    def trade(self, price):
        self.price_history.append(price)
        if len(self.price_history) < self.optimization_period:
            return OrderSide.NO_OP
        elif len(self.price_history) == self.optimization_period:
            if self.async_optimization:
                self.optimize_async_result = self.tr.optimize_multiprocess_async(
                    self.price_history[:], ema_const_range=15
                )
            else:
                self.tr.optimize_multiprocess(self.price_history[:], ema_const_range=15)
            return OrderSide.NO_OP
        elif self.async_optimization:
            if not self.optimize_async_result.ready():
                return OrderSide.NO_OP

        traded = False
        self.quote *= (
            1
            + (self.price_history[-1] - self.price_history[-2]) / self.price_history[-2]
        )

        action = self.tr.action(self.price_history[-1])
        if action == OrderSide.BUY:  # buy
            if self.base > 0:
                self.quote += 0.999 * self.base
                self.base = 0
                self.num_buys += 1
                traded = True
        elif action == OrderSide.SELL:  # sell
            if self.quote > 0:
                self.base += 0.999 * self.quote
                self.quote = 0
                self.num_sells += 1
                traded = True

        self.base_arr.append(self.base)
        self.quote_arr.append(self.quote)

        if len(self.price_history) % self.optimization_period == 0:
            if self.async_optimization:
                self.tr.optimize_multiprocess_async(
                    self.price_history[-self.optimization_period : -1],
                    ema_const_range=21,
                )
            else:
                self.tr.optimize_multiprocess(
                    self.price_history[-self.optimization_period : -1],
                    ema_const_range=21,
                )

        if traded:
            return action
        return OrderSide.NO_OP
