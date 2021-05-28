import numpy as np
import multiprocessing

from typing import List, Tuple, Optional

from order_side import OrderSide


class EMA_strategy:
    """Class to hold EMA trading logic

    Why even have a class for this?
    - Easier management of previous EMA values, prices values, e.t.c.
    """

    def __init__(self, ema_smoothing_const: float = 0.1, period_range: int = 2):
        """
        params:
            ema_smoothing_const - constant, determined by optimize. 0.1 is assumed to be good initial guess
            period_range - number of periods over which the EMA is calculated
        """
        self.ema_smoothing_const_1: float = ema_smoothing_const
        self.ema_smoothing_const_2: float = ema_smoothing_const
        self.period_range_1: int = period_range
        self.period_range_2: int = period_range - 1
        self._prev_ema_val_1: Optional[float] = None  # default initial EMA value to 0
        self._prev_ema_val_2: Optional[float] = None  # default initial EMA value to 0
        self._pool = multiprocessing.Pool(multiprocessing.cpu_count() - 1)

    def ema(
        self,
        cur_price: float,
        prev_ema: float,
        ema_smoothing_const: float,
        period_range: int,
    ):
        return cur_price * ema_smoothing_const / (1 + period_range) + prev_ema * (
            1 - ema_smoothing_const / (1 + period_range)
        )

    def ema_pair(self, cur_price: float) -> float:
        "Simply return EMA values at given cur_price"

        # if this is the first call to EMA, set the previous ema to cur price
        self._prev_ema_val_1 = (
            cur_price if self._prev_ema_val_1 is None else self._prev_ema_val_1
        )
        self._prev_ema_val_2 = (
            cur_price if self._prev_ema_val_2 is None else self._prev_ema_val_2
        )

        ema1 = self.ema(
            cur_price,
            self._prev_ema_val_1,
            self.ema_smoothing_const_1,
            self.period_range_1,
        )
        ema2 = self.ema(
            cur_price,
            self._prev_ema_val_2,
            self.ema_smoothing_const_2,
            self.period_range_2,
        )

        self._prev_ema_val_1 = ema1
        self._prev_ema_val_2 = ema2

        return ema1, ema2

    def action(self, cur_price: float) -> int:
        """
        Returns:
             1 if should buy
             0 if do nothing
            -1 if should sell
        """
        ema1, ema2 = self.ema_pair(cur_price)
        if ema2 > ema1:
            return OrderSide.BUY
        elif ema1 > ema2:
            return OrderSide.SELL
        return OrderSide.NO_OP

    def set_params(
        self,
        ema_smoothing_const_1: float,
        period_range_1: float,
        ema_smoothing_const_2: int,
        period_range_2: int,
        best_score: Optional[float] = None,
    ):
        print_str = f"SET PARAMS: {ema_smoothing_const_1} {period_range_1} {ema_smoothing_const_1} {period_range_2}"
        if best_score is not None:
            print_str += f"SCORE: {best_score}"
        print(print_str)

        self.ema_smoothing_const_1: float = ema_smoothing_const_1
        self.ema_smoothing_const_2: float = ema_smoothing_const_2
        self.period_range_1: float = period_range_1
        self.period_range_2: float = period_range_2

    def get_params(self):
        return (
            self.ema_smoothing_const_1,
            self.period_range_1,
            self.ema_smoothing_const_2,
            self.period_range_2,
        )

    def optimize(self, prices: np.array, ema_const_range: int = 10):
        """
        Optimizes ema params over prices
        """
        for j in range(ema_const_range):
            _, parameters = _optimize_given_j(j, prices, ema_const_range)
        self.set_params(*parameters)

    def optimize_multiprocess(self, prices: np.array, ema_const_range: int = 10):
        """
        Optimizes ema params over prices
        """
        num_cores = multiprocessing.cpu_count()
        best_score, best_params = max(
            self._pool.starmap(
                _optimize_given_j,
                zip(
                    range(ema_const_range),
                    [prices] * ema_const_range,
                    [ema_const_range] * ema_const_range,
                ),
            )
        )
        self.set_params(*best_params)

    def optimize_multiprocess_async(self, prices: np.array, ema_const_range: int = 10):
        """
        Optimizes ema params over prices,
        """

        def cb(results):
            best_score, best_params = max(results)
            self.set_params(*best_params, best_score=best_score)

        def err_cb(err):
            return

        return self._pool.starmap_async(
            _optimize_given_j,
            zip(
                range(ema_const_range),
                [prices] * ema_const_range,
                [ema_const_range] * ema_const_range,
            ),
            callback=cb,
            error_callback=err_cb,
        )


def _optimize_given_j(j: int, prices: list, ema_const_range: int = 10):
    def ema(
        cur_price: float,
        prev_ema: float,
        ema_smoothing_const: float,
        period_range: int,
    ):
        return cur_price * ema_smoothing_const / (1 + period_range) + prev_ema * (
            1 - ema_smoothing_const / (1 + period_range)
        )

    best_score = 0

    best_ema_smoothing_const_1 = 0
    best_period_range_1 = 0
    best_ema_smoothing_const_2 = 0
    best_period_range_2 = 0

    prev_price, *prices = prices
    for k in range(10):
        for l in range(10):
            for m in range(10):
                base = 100
                quote = 0

                d1 = j
                d2 = k
                ema_smoothing_const_1 = l / 10
                ema_smoothing_const_2 = m / 10

                prev_ema1 = prev_price
                prev_ema2 = prev_price

                for i, price in enumerate(prices):

                    # trading logic
                    ema1 = ema(price, prev_ema1, ema_smoothing_const_1, d1)
                    ema2 = ema(price, prev_ema2, ema_smoothing_const_2, d2)

                    percent_change = (price - prev_price) / prev_price
                    quote *= 1 + percent_change

                    if ema2 > ema1:
                        # buy
                        if base > 0:
                            quote += 0.999 * base
                            base = 0
                    elif ema1 < ema2:
                        # sell
                        if quote > 0:
                            base += 0.999 * quote
                            quote = 0

                    prev_price = price

                if quote + base > best_score:
                    best_score = quote + base
                    best_period_range_1 = d1
                    best_period_range_2 = d2
                    best_ema_smoothing_const_1 = ema_smoothing_const_1
                    best_ema_smoothing_const_2 = ema_smoothing_const_2

    return best_score, (
        best_ema_smoothing_const_1,
        best_period_range_1,
        best_ema_smoothing_const_2,
        best_period_range_2,
    )
