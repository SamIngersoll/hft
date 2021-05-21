import numpy as np

from typing import List, Tuple, Optional


class EMA_trader:
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
        if self._prev_ema_val_1 is None or self._prev_ema_val_2 is None:
            self._prev_ema_val_1 = cur_price
            self._prev_ema_val_2 = cur_price

        ema_1 = self.ema(
            cur_price,
            self._prev_ema_val_1,
            self.ema_smoothing_const_1,
            self.period_range_1,
        )
        ema_2 = self.ema(
            cur_price,
            self._prev_ema_val_2,
            self.ema_smoothing_const_2,
            self.period_range_2,
        )
        return ema_1, ema_2

    def action(self, cur_price: float) -> float:
        """
        Returns:
            1 if should buy
            0 if do nothing
            -1 if should sell
        """
        ema1, ema2 = self.ema_pair(cur_price)
        if ema1 > ema2:
            return 1
        elif ema2 > ema1:
            return -1
        return 0

    def optimize(self, prices: np.array):
        """
        Optimizes ema params over prices
        """
        best_score = 0

        best_ema_smoothing_const_1 = 0
        best_period_range_1 = 0
        best_ema_smoothing_const_2 = 0
        best_period_range_2 = 0

        for j in range(0, 10):
            for k in range(0, 10):
                for l in range(0, 10):
                    for m in range(0, 10):
                        cash = 100
                        doge = 0

                        d1 = j
                        d2 = k

                        ema_smoothing_const_1 = l / 10
                        ema_smoothing_const_2 = m / 10

                        ema_hist1 = [0] * len(t)
                        ema_hist2 = [0] * len(t)
                        ema_hist1[0] = p[0]
                        ema_hist2[0] = p[0]

                        for i in range(1, len(p)):
                            price = p[i]

                            # trading logic
                            ema_hist1[i] = self.ema(
                                price, ema_hist1[i - 1], ema_smoothing_const_1, d1
                            )
                            ema_hist2[i] = self.ema(
                                price, ema_hist2[i - 1], ema_smoothing_const_2, d2
                            )

                            percent_change = (price - prev_price) / prev_price
                            doge *= 1 + percent_change

                            if ema_hist2[i] < ema_hist1[i]:
                                # buy
                                if cash > 0:
                                    doge += 0.999 * cash
                                    cash -= cash
                                    activity[i] = buy

                            if ema_hist2[i] > ema_hist1[i]:
                                # sell
                                if doge > 0:
                                    cash += 0.999 * doge
                                    doge -= doge
                                    activity[i] = sell

                            prev_price = price

                        if doge + cash > best_score:
                            best_score = doge + cash
                            best_period_range_1 = d1
                            best_period_range_2 = d2
                            best_ema_smoothing_const_1 = ema_smoothing_const_1
                            best_ema_smoothing_const_2 = ema_smoothing_const_2

        return (
            best_ema_smoothing_const_1,
            best_period_range_1,
            best_ema_smoothing_const_2,
            best_period_range_2,
        )
