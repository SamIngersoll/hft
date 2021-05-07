# hft

## TODOS

- Buy a coin through API (to test functionality)
- Set up automatic order creation.
    - For both buy and sell,
        - Choose amount that we want to trade
        - Confirm that it conforms to the coin's filters
        - If it doesn't, modify the order so it does
    - Decide on order type (e.g. Limit vs. Market)
        - Limit Order: Create a bid/ask, someone else fills it
            - No/Reduced fees since we would be "market makers"
            - No garuntee of the order filling. Therefore, would have to figure out contingencies for this case, and price our bid/ask such that there will be a high probability of the order actually filling (i.e. maybe 99% of the best bid/ask? this could be tested w/ small orders)
        - Market Order: Immediately fills the bid/ask at the best market price
            - Fees since we would be "market takers"
            - "Slippage" can increase price / fees (if you order 100, but best limit order on market is for a quantity of 50, the rest of the order would be filled at the worse limit order prices)
            - Immediate filling would allow us to make more trades per unit time, potentially beating the fees / worse prices. Don't know of a way to evaluate this for certain other than raw testing.
- Structure EMA algo to work w/ API stuff
    - Dunno the best architecture here