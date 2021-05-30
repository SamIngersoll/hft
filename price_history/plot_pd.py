#! /usr/bin/env python3

import sys
import numpy as np
import matplotlib.pyplot as plt



if len(sys.argv) < 2:
    print("usage: ./plot_pd.py <file1> [<file2> [<file3> ...]]")
    exit(1)


for f in sys.argv[1:]:
    try:
        data = np.load(f, allow_pickle=True)
    except OSError:
        print(f"{f} not picklable - skipping...")
        continue
    plt.plot(data)
    plt.xlabel("time")
    plt.ylabel("price")
    plt.show()

