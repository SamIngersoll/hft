# hft


## Structure

How I view the structure:

```
-----------------+
Binance Websocket| --> Trader --> Strategy
-----------------+        ^           ^
						  | Takes websocket, prepares/feeds data to strategy,
						  | takes order instructions from strategy (e.g. buy/sell)
						  | and executes orders
									  | Takes datastream via `trade` method, and for
									  | each execution, it returns "Orderside.BUY",
									  | "Orderside.SELL", or "Orderside.NO_OP"
```

Right now, it is not generalized/modularized.

## TODOS

- ~~Buy a coin through API (to test functionality)~~ Done
- ~~Structure EMA algo to work w/ API stuff~~
    - Dunno the best architecture here - prototype is working. I think a good goal would be to make it easy to quickly test with various parameters, strategies, e.t.c.
	- bl.py 
		- Sets up / handles websocket, executes orders, e.t.c.
		- Would be good to have some sort of JSON/yaml config for trading strategies. e.g. the json config would specify stock, strategy parameters, and (stretch goal) stop-loss levels, configs for trading out of currencies, e.t.c.
	- trader.py
		- takes orders, handles optimization/training of strategies, e.t.c.
	- ema\_strategy.py
		- strategy for trading. actual trading logic is here
- Set up automatic order creation.
    - For both buy and sell,
        - Choose amount that we want to trade
        - Confirm that it conforms to the coin's filters
        - If it doesn't, modify the order so it does (how?)
    - Decide on order type (e.g. Limit vs. Market)
        - FOR NOW, MARKET ORDER IS THE WAY - depending on state of system, try limit
        - Limit Order: Create a bid/ask, someone else fills it
            - No/Reduced fees since we would be "market makers"
            - No garuntee of the order filling. Therefore, would have to figure out contingencies for this case, and price our bid/ask such that there will be a high probability of the order actually filling (i.e. maybe 99% of the best bid/ask? this could be tested w/ small orders)
        - Market Order: Immediately fills the bid/ask at the best market price
            - Fees since we would be "market takers"
            - "Slippage" can increase price / fees (if you order 100, but best limit order on market is for a quantity of 50, the rest of the order would be filled at the worse limit order prices)
            - Immediate filling would allow us to make more trades per unit time, potentially beating the fees / worse prices. Don't know of a way to evaluate this for certain other than raw testing.

## Limitations

- When trading on the DOGEBTC market, there is a min notional value required for the trade of 0.0001 BTC (~\$5.75 USD), the lot size for selling DOGE is 1 (i.e. can't sell fractional doge). This are limiting factors. Here are all the DOGEBTC filters:

```json
'filters': [
  {'filterType': 'PRICE_FILTER',
   'minPrice': '0.00000001',
   'maxPrice': '1000.00000000',
   'tickSize': '0.00000001'},
  {'filterType': 'PERCENT_PRICE',
   'multiplierUp': '5',
   'multiplierDown': '0.2',
   'avgPriceMins': 5},
  {'filterType': 'LOT_SIZE',
   'minQty': '1.00000000',
   'maxQty': '90000000.00000000',
   'stepSize': '1.00000000'},
  {'filterType': 'MIN_NOTIONAL',
   'minNotional': '0.00010000',
   'applyToMarket': True,
   'avgPriceMins': 5},
  {'filterType': 'ICEBERG_PARTS', 'limit': 10},
  {'filterType': 'MARKET_LOT_SIZE',
   'minQty': '0.00000000',
   'maxQty': '19785596.74339360',
   'stepSize': '0.00000000'},
  {'filterType': 'MAX_NUM_ORDERS', 'maxNumOrders': 200},
  {'filterType': 'MAX_NUM_ALGO_ORDERS', 'maxNumAlgoOrders': 5}
]
```
