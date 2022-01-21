import math
import time
import requests
import pandas as pd
import numpy as np

def fetch_thegraph_data(strategy):

    days = 30
    #get unix timestamp 30 days ago
    timestamp = int(time.time()) - (days * 24 * 60 * 60)      
    
   
    query = """
            {
                pool(id: "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640")
                    {
                    poolDayData (where: { date_gte : """ + str(timestamp) + """} ) {
                    id
                    date
                    tvlUSD
                    feesUSD
                    open
                    high
                    low
                    close
                    volumeUSD
                    liquidity
                    sqrtPrice
                    token0Price
                    token1Price
                    volumeToken0
                    volumeToken1
                    txCount
                    }
                }
            }
            """

    print('request to the graph')
    request = requests.post('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
                                    '', json={'query': query})

    print(request.json())
    data_dct = request.json()['data']['pool']['poolDayData']

    data_df = pd.DataFrame(data_dct)

    data_df["date"] = pd.to_datetime(data_df["date"], unit = "s")

    data_df[[col for col in data_df.columns if col not in ("date","id")]] = data_df[[col for col in data_df.columns if col not in ("date","id")]].astype(float)

    data_df[["pct_change_close"]] = data_df[["close"]].pct_change(periods = 1)

    data_df.replace([np.inf, -np.inf], np.nan, inplace=True)
    last_row = data_df.iloc[-1]
    
    std_deviation = data_df[["pct_change_close"]].std().iloc[-1]
    print("std deviation is " + str(std_deviation))

    tick_spacing = strategy.tickSpacing()
    print('tick_spacing is: ' + str(tick_spacing))
    tick = strategy.getTick()
    price = (tick / (1 << 96))**2
    print('tick is: ' + str(tick))
    print(str(1.0001 ** tick))

    base_lower_price = (1 - std_deviation) * price
    limit_lower_price = (1 - std_deviation * 0.25) * price

    base_lower_tick = math.log(1/base_lower_price * 10e12, 1.0001)
    limit_lower_tick = math.log(1/limit_lower_price * 10e12, 1.0001)

    base_width =  base_lower_tick - tick
    limit_width = limit_lower_tick - tick

    base_width = int(math.ceil(int(base_width) / tick_spacing)) * tick_spacing
    limit_width = int(math.ceil(int(limit_width) / tick_spacing)) * tick_spacing

    print('base_width is ' + str(base_width))
    print('limit_width is ' + str(limit_width))

    final_data_dict = {
        'priceGraph': last_row['close'],
        'volume': last_row['volumeUSD'],
        'liquidity': last_row['liquidity'],
        'fees_pool': last_row['feesUSD'],
        'limit_lower': limit_width,
        'base_lower': base_width,
    }

    return final_data_dict

