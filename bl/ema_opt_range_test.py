#! /usr/bin/env python3

import argparse
import numpy as np
import matplotlib.pyplot as plt

from trader import Trader

parser = argparse.ArgumentParser("beginner's luck")
parser.add_argument(
    "-f",
    metavar="--file",
    type=str,
    help="path to .npy file - should be array of prices over time",
    dest="file",
)


if __name__ == "__main__":
    opt_periods = [200, 500, 1000, 1500, 2000, 5000]

    args = parser.parse_args()

    print(f"loading {args.file}...")
    data = np.load(args.file, allow_pickle=True)

    value_block = np.zeros((len(opt_periods), len(data)))

    for j, period in enumerate(opt_periods):
        print(f"optimizing with period {period}")
        t = Trader(async_optimization=False, optimization_period=period)
        try:
            for i, p in enumerate(data):
                t.trade(p)
                value_block[j, i] = t.base + t.quote
        except Exception as e:
            print(e)

    import matplotlib.pyplot as plt

    fig, axs = plt.subplots(7)
    axs[0].plot(t.price_history)
    for k in range(len(opt_periods)):
        axs[k + 1].title.set_text(f"Opt Period {opt_periods[k]}")
        axs[k + 1].plot(value_block[k, :])
    plt.show()
