import numpy as np

from Typing import List, Tuple


def ema(
    cur_price: float,
    prev_period_ema: float,
    ema_smoothing_const: float,
    num_periods: float,
):
    """
    C = Current Price
    P = Previous periods EMA (A SMA is used for the first periods calculations)
    K = Exponential smoothing constant
    D = length of moving average in days
    """
    return cur_price * ema_smoothing_const / (1 + num_periods) + prev_period_ema * (
        1 - ema_smoothing_const / (1 + num_periods)
    )


def bollinger_bands(prices: float, X: float = 2) -> Tuple[float]:
    """Returns avg, lower bollinger band, upper bollinger band

    params:
        prices: list of prices over previous 'num_periods'
        X: bollinger band constant (how abt. std_dev_multiplier for a name?)
    """
    avg = sum(prices) / len(prices)
    std_dev = np.std(prices)
    UB = avg + X * std_dev
    LB = avg - X * std_dev
    return avg, LB, UB

