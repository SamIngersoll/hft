#! /usr/bin/env python3

"""
    ____             _                      _          __              __
   / __ )___  ____ _(_)___  ____  ___  ____( )_____   / /  __  _______/ /__
  / __  / _ \/ __ `/ / __ \/ __ \/ _ \/ ___/// ___/  / /  / / / / ___/ //_/
 / /_/ /  __/ /_/ / / / / / / / /  __/ /    (__  )  / /__/ /_/ / /__/ ,<
/_____/\___/\__, /_/_/ /_/_/ /_/\___/_/    /____/  /_____|__,_/\___/_/|_|
           /____/
"""

import sys
import argparse
import time, toml
import numpy as np
import matplotlib.pyplot as plt

from trader import Trader

from binance.client import Client
from binance import ThreadedWebsocketManager


parser = argparse.ArgumentParser("beginner's luck")
parser.add_argument(
    "-s",
    "--symbol",
    type=str,
    help="ticker symbol (e.g. DOGEBTC) does not error for invalid symbols",
    dest="symbol",
)
parser.add_argument(
    "-f",
    "--file",
    type=str,
    help="path to .npy file - should be array of prices over time",
    dest="file",
)
parser.add_argument(
    "-p",
    "--print_period",
    type=float,
    help="period between printing info to stdout [s]",
    default=60,
)
parser.add_argument(
    "-o",
    "--optimzation_period",
    type=int,
    help="number of prices over which EMA is optimized",
    default=1500,
)
parser.add_argument(
    "-L",
    "--LIVE",
    help="run socket on live market instead of test net",
    action="store_true",
)


def socket_callback(bm, symbol, msg):
    if msg["e"] == "error":
        # close and restart the socket
        print(f"websocket error encountered: {msg['e']}")
        print(f"attempting restart...")
        bm.stop_socket(symbol)
        bm.start_symbol_ticker_socket(
            symbol=symbol, callback=lambda msg: socket_callback(bm, symbol, msg)
        )
    else:
        t.trade(float(msg["c"]))


# everything in main block due to multiprocessing "fork" behaviour being weird
if __name__ == "__main__":
    args = parser.parse_args()

    # We need either a symbol (-s) or a file (-f)
    if bool(args.symbol) == bool(args.file):
        parser.print_help(sys.stderr)
        print(
            "\neither a symbol (e.g. DOGEBTC) or a file path to a .npy file must be supplied"
        )
        exit(1)

    cfg = toml.load("../api/configuration.toml")
    if args.LIVE:
        confirmation_str = "are you SURE you want to trade live? actual money will be traded: [yes/no] "
        if input(confirmation_str) != "yes":
            print("good choice!")
            exit(1)
        print("creating live client...")
        pkey = cfg["auth"]["pkey"]
        skey = cfg["auth"]["skey"]
        client = Client(pkey, skey)
    else:
        print("creating test client...")
        pkey = cfg["testnet"]["pkey"]
        skey = cfg["testnet"]["skey"]
        client = Client(pkey, skey, testnet=True)

    if args.symbol:
        symbol = args.symbol.upper()
        if symbol not in [c["symbol"] for c in client.get_exchange_info()["symbols"]]:
            print(
                "symbol not found in binance exchange - double check for typos, and that the symbol is supported"
            )
            exit(1)

        t = Trader(
            symbol,
            client,
            async_optimization=True,
            optimization_period=args.optimzation_period,
        )

        print(f"starting socket for {symbol}...")
        bm = ThreadedWebsocketManager(api_key=pkey, api_secret=skey)
        bm.start()
        bm.start_symbol_ticker_socket(
            symbol=symbol,
            callback=lambda msg: socket_callback(bm, symbol, msg),
        )
        print("socket started\n")

        try:
            while True:
                print("\n" + time.ctime())
                print(f"Price History Len: {len(t.price_history)}")
                print(f"base: {t.base_quantity}\t\tquote: {t.quote_quantity}")
                print(f"buys: {t.num_buys}\t\tsells: {t.num_sells}\n")
                time.sleep(args.print_period)
        except KeyboardInterrupt:
            # halt the worker pool
            t.strategy._pool.terminate()
            t.strategy._pool.join()
        else:
            t.strategy._pool.close()
            t.strategy._pool.join()

        # save data?
        res = input("save price history? [y/n] ")
        if res.lower() == "y":
            datestamp = time.ctime().replace(" ", "_")
            np.save(
                f"../price_history/{symbol}_{datestamp}_{len(t.price_history)}s",
                np.asarray(t.price_history),
            )

        # you gotta press ctrl-c again, i think cause i am halting the worker pool wrong
        print("ctrl-c")
        # Transfer dust? somethign like client.transfer_dust(asset="BNB")

    # This is currently broken - need to create a trader
    # class for just file backtrading. Actually, could just
    # hop back some commits and yoink that trader class.
    elif args.file:
        t = Trader(
            symbol,
            client,
            async_optimization=False,
            optimization_period=args.optimzation_period,
        )

        print(f"loading {args.file}...")
        data = np.load(args.file, allow_pickle=True)

        for i, p in enumerate(data):
            t.trade(p)
            val.append(t.base + t.quote)

            if i % args.print_period == 0:
                print("\n" + time.ctime())
                print(f"base: {t.base}\t\tquote: {t.quote}")
                print(f"buys: {t.num_buys}\t\tsells: {t.num_sells}\n")

        val = np.asarray(t.base_arr) + np.asarray(t.quote_arr)

        fig, axs = plt.subplots(2)
        axs[0].plot(data)
        axs[1].plot(val)
        plt.show()

    else:
        print("how the heck did you get here? submit an issue for this please!!!")
