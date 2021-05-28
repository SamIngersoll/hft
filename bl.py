#! /usr/bin/env python3

import time, toml
import numpy as np

from trader import Trader

from binance import ThreadedWebsocketManager

from twisted.internet import reactor


if __name__ == "__main__":  # everything in main block due to multiprocessing errors
    cfg = toml.load("api/configuration.toml")
    pkey = cfg["auth"]["pkey"]
    skey = cfg["auth"]["skey"]

    t = Trader(async_optimization=True, optimization_period=5000)

    def cb(bm, stream_name, msg):
        if msg["e"] == "error":
            # close and restart the socket
            print(f"websocket error encountered: {msg['e']}")
            print(f"attempting restart...")
            bm.stop_socket(stream_name)
            bm.start_symbol_ticker_socket(
                symbol="DOGEBTC", callback=lambda msg: cb(bm, "DOGEBTC", msg)
            )
        t.trade(float(msg["c"]))

    try:
        print("starting socket...")
        bm = ThreadedWebsocketManager(api_key=pkey, api_secret=skey)
        bm.start()
        bm.start_symbol_ticker_socket(
            symbol="DOGEBTC", callback=lambda msg: cb(bm, "DOGEBTC", msg)
        )
        print("socket started\n")

        while True:
            print("\n" + time.ctime())
            print(f"Price History Len: {len(t.price_history)}")
            print(f"base: {t.base}\t\tquote: {t.quote}")
            print(f"buys: {t.num_buys}\t\tsells: {t.num_sells}\n")
            time.sleep(60)

    except KeyboardInterrupt:
        # halt the worker pool for optimization
        t.tr._pool.terminate()
        t.tr._pool.join()

        # save data?
        res = input("save price history? [y/n] ")
        if res.lower() == "y":
            datestamp = time.ctime().replace(" ", "_")
            np.save(
                f"price_history/price_data_{datestamp}_{len(t.price_history)}s",
                np.asarray(t.price_history),
            )

        # you gotta press ctrl-c again
        print("ctrl-c")
