#! /usr/bin/env python3

import argparse
import time, toml
import numpy as np

from trader import Trader

from binance import ThreadedWebsocketManager


parser = argparse.ArgumentParser("beginner's luck")
parser.add_argument(
    "symbol",
    metavar="symbol",
    type=str,
    help="ticker symbol - e.g. DOGEBTC. Note: does not error for invalid symbols",
)
parser.add_argument(
    "-p", metavar="--print_period", type=float, help="period between printing info to stdout [s]", default=60
)
parser.add_argument(
    "-o", metavar="--optimzation_period", type=int, help="number of prices over which we optimize [trades]", default=1000
)


if __name__ == "__main__":  # everything in main block due to multiprocessing errors
    args = parser.parse_args()
    symbol = args.symbol

    t = Trader(async_optimization=True, optimization_period=args.o)

    cfg = toml.load("api/configuration.toml")
    pkey = cfg["auth"]["pkey"]
    skey = cfg["auth"]["skey"]

    def cb(bm, symbol, msg):
        if msg["e"] == "error":
            # close and restart the socket
            print(f"websocket error encountered: {msg['e']}")
            print(f"attempting restart...")
            bm.stop_socket(symbol)
            bm.start_symbol_ticker_socket(
                symbol=symbol, callback=lambda msg: cb(bm, symbol, msg)
            )
        else:
            t.trade(float(msg["c"]))

    print(f"starting socket for {symbol}...")
    bm = ThreadedWebsocketManager(api_key=pkey, api_secret=skey)
    bm.start()
    bm.start_symbol_ticker_socket(
        symbol=symbol, callback=lambda msg: cb(bm, symbol, msg)
    )

    print("socket started\n")

    try:
        while True:
            print("\n" + time.ctime())
            print(f"Price History Len: {len(t.price_history)}")
            print(f"base: {t.base}\t\tquote: {t.quote}")
            print(f"buys: {t.num_buys}\t\tsells: {t.num_sells}\n")
            time.sleep(args.p)

    except KeyboardInterrupt:
        # halt the worker pool for optimization
        t.tr._pool.terminate()
        t.tr._pool.join()

        # save data?
        res = input("save price history? [y/n] ")
        if res.lower() == "y":
            datestamp = time.ctime().replace(" ", "_")
            np.save(
                f"price_history/{symbol}_{datestamp}_{len(t.price_history)}s",
                np.asarray(t.price_history),
            )

        # you gotta press ctrl-c again
        print("ctrl-c")
