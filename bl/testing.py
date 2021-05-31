#! /usr/bin/env python3

import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from trader import Trader
from order_side import OrderSide
from ema_strategy import EMA_strategy


plt.rcParams["figure.dpi"] = 200
plt.rcParams["figure.figsize"] = (20,10)
plt.rcParams.update({'font.size': 18})


if __name__ == '__main__':
    t = Trader()

    history = pd.read_csv('../historical_data/binance_DOGEBTC_1m.csv')
    brices = history['open'].tolist()

    values = []

    for p in brices:
        t.trade(p)
        values.append(t.base + t.quote)

    plt.plot(values)
    plt.show()
