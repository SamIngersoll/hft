#! /usr/bin/env python3

import time, toml
import numpy as np

from trader import Trader

from binance.client import Client
from binance.websockets import BinanceSocketManager


if __name__ == "__main__":
    cfg = toml.load("api/configuration.toml")
    pkey = cfg["auth"]["pkey"]
    skey = cfg["auth"]["skey"]
    client = Client(pkey, skey)

    t = Trader(async_optimization=True)

    def cb(msg):
        t.trade(float(msg["c"]))

    try:
        print("starting socket")
        bm = BinanceSocketManager(client)
        bm.start_symbol_ticker_socket("DOGEBTC", cb)
        bm.start()
        print("socket started\n")
        while True:
            print(time.ctime())
            print(f"Price History Len: {len(t.price_history)}")
            print(f"base: {t.base}\t\tquote: {t.quote}", end="\n")
            time.sleep(60)

    except KeyboardInterrupt:
        t.tr._pool.terminate()
        t.tr._pool.join()
        res = input("save price history? [y/n] ")
        if res.lower() == "y":
            datestamp = time.ctime().replace(" ", "_")
            np.save(
                f"price_history/price_data_{datestamp}_{len(t.price_history)}s",
                np.asarray(t.price_history),
            )
        print("ctrl-c")
