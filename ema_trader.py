import numpy as np

from enum import Enum
from multiprocessing import Pool
from typing import List, Tuple, Optional


class EMA_trader:
    """Class to hold EMA trading logic

    Why even have a class for this?
    - Easier management of previous EMA values, prices values, e.t.c.
    """

    class OrderSide(Enum):
        BUY = 1
        SELL = 2
        NO_OP = 3

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
            return self.OrderSide.BUY
        elif ema1 > ema2:
            return self.OrderSide.SELL
        return self.OrderSide.NO_OP

    def set_params(
        self,
        ema_smoothing_const_1: float,
        period_range_1: float,
        ema_smoothing_const_2: int,
        period_range_2: int,
    ):
        self.ema_smoothing_const_1: float = ema_smoothing_const_1
        self.ema_smoothing_const_2: float = ema_smoothing_const_2
        self.period_range_1: float = period_range_1
        self.period_range_2: float = period_range_2

    def optimize(self, prices: np.array):
        """
        Optimizes ema params over prices
        """
        for j in range(10):
            best_score, (
                best_ema_smoothing_const_1,
                best_period_range_1,
                best_ema_smoothing_const_2,
                best_period_range_2,
            ) = _optimize_given_j(j, prices)

        print(
            f"{best_score:.3f}",
            (
                best_ema_smoothing_const_1,
                best_period_range_1,
                best_ema_smoothing_const_2,
                best_period_range_2,
            ),
        )
        return (
            best_ema_smoothing_const_1,
            best_period_range_1,
            best_ema_smoothing_const_2,
            best_period_range_2,
        )

    def optimize_threaded(self, prices: np.array):
        """
        Optimizes ema params over prices
        """
        with Pool(10) as p:
            best_score, best_params = max(
                p.starmap(_optimize_given_j, zip(range(10), [prices] * 10))
            )
            print(f"{best_score:.3f}", best_params)
            return best_params


def _optimize_given_j(j, prices):
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
