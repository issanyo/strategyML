from pandas.core import base
from web3 import Web3, middleware
from web3.gas_strategies.time_based import medium_gas_price_strategy

import binascii
import requests
from datetime import datetime, timedelta
import json
import numpy as np
from utils import get_contract_abi, connect_db
import os
import psycopg2
import pandas as pd
import math
import time
import numpy as np
import matplotlib

keeper = '0xffa9FDa3050007645945e38E72B5a3dB1414A59b'
pk = os.environ['PK']
WEB3_INFURA_PROJECT_ID = os.environ['WEB3_INFURA_PROJECT_ID']

def test_transaction():
    web3 = Web3(Web3.HTTPProvider('https://ropsten.infura.io/v3/' + WEB3_INFURA_PROJECT_ID))
    balance = web3.eth.get_balance(keeper)

    print(balance)
    receiverAccount = '0xaaB5a17c0d9d09632F013d8b5E2353A77710dDc1'

    nonce = web3.eth.getTransactionCount(keeper)

    transaction  = {
        'to': receiverAccount,
        'value': 370000000000000,
        'gas': 2000000,
        'chainId': 3,
        'gasPrice': 200000000000,
        'nonce': nonce
    }
    
    
    signed_transaction = web3.eth.account.sign_transaction(transaction, pk)
    
    print('signed transaction hash is ' + str(binascii.hexlify(signed_transaction.hash)))
    hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    web3.eth.wait_for_transaction_receipt(hash)


    print('transaction returns hash as: ' + str(hash))

    newBalance = web3.eth.get_balance(keeper)
    print(newBalance)


def fetch():
    abi = get_contract_abi()
    con = connect_db()

    web3 = Web3(Web3.HTTPProvider('https://ropsten.infura.io/v3/' + WEB3_INFURA_PROJECT_ID))
    web3.eth.set_gas_price_strategy(medium_gas_price_strategy)

    web3.middleware_onion.add(middleware.time_based_cache_middleware)
    web3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
    web3.middleware_onion.add(middleware.simple_cache_middleware)
    vault = web3.eth.contract('0x3047B2b49f104F38f3b3f1AC9b8Df1C62726251E', abi=abi['AlphaVault'])
    strategy = web3.eth.contract('0xa5EeD50E39daFF57F5b7480dF6E65391C44eF49C', abi=abi['DynamicRangesStrategy'])

    theGraphData = fetch_thegraph_data(strategy)

    cur = con.cursor()

    last_rebalance = get_last_rebalance(cur)
    timestamp = datetime.now()

    try:
        if timestamp - last_rebalance > timedelta(hours=48):
            rebalance(theGraphData['limit_lower'], theGraphData['base_lower'], strategy, web3)
            last_rebalance = timestamp
            rebalance_check = True
        else:
            rebalance_check = False
    except Exception as e:
        print(e)

    total0, total1 = vault.functions.getTotalAmounts().call()

    baseLower = vault.functions.baseLower().call()
    baseUpper = vault.functions.baseUpper().call()

    limitUpper = vault.functions.limitUpper().call()
    limitLower = vault.functions.limitLower().call()
        
    outstandingShares = vault.functions.totalSupply().call()
    
    tick = strategy.functions.getTick().call()
    
    token0 = web3.eth.contract(vault.functions.token0().call(), abi=abi['MockToken'])
    token1 = web3.eth.contract(vault.functions.token1().call(), abi=abi['MockToken'])

    decimals_token_0 = token0.functions.decimals().call()
    decimals_token_1 = token1.functions.decimals().call()

    price = 1.001 ** tick * 10 ** (decimals_token_0 - decimals_token_1)

    tvl = price * total1
    print('total0: ' + str(total0) + '\n' + 'total1: ' + str(total1) + '\n' + 'baseLower is ' + str(baseLower) + '\n' + 'baseUpper is ' + str(baseUpper) + '\n' + 'limitUpper is ' + str(limitUpper) + '\n' + 'limitLower is ' + str(limitLower) + '\n' + 'outstanding shares is ' + str(outstandingShares) + '\n' + 'tick is ' + str(tick) + '\n' + 'price is ' + str(price) + '\n' + 'tvl is ' + str(tvl) + '\n')

    
    try:
        cur.execute("INSERT INTO keeperbot_data (token0_quantity, token1_quantity, \"baseLower\", \"baseUpper\", \"limitUpper\", \"limitLower\", \"totalSupply\", \"priceStrategy\", tvl, pool_address, strategy_address, timestamp, price_graph, volume, liquidity, fees_pool, rebalance_check, rebalance_timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (total0, total1, baseLower, baseUpper, limitUpper, limitLower, outstandingShares, price, tvl, '0x624633fD2Eff00cBFC7294CABD80303b12C5fD9d', '0x4Bb99cfEe541C66a79D4DaeB4431BCfe8de1d410', timestamp, theGraphData['priceGraph'], theGraphData['volume'], theGraphData['liquidity'], theGraphData['fees_pool'], rebalance_check, last_rebalance))
        con.commit()
        print('Data successfully inserted')
    except psycopg2.Error as e:
        print(e)
        con.rollback()

    con.close()


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

    tick_spacing = strategy.functions.tickSpacing().call()
    print('tick_spacing is: ' + str(tick_spacing))
    tick = strategy.functions.getTick().call()
    print('tick is: ' + str(tick))
    print(str(1.0001 ** tick))

    base_lower_price = (1 - std_deviation) * data_df[['close']].iloc[-1]
    limit_lower_price = (1 - std_deviation * 0.25) * data_df[['close']].iloc[-1]

    print('data df close is: ' + str(data_df[['close']].iloc[-1]))
    print('base_lower_price is ' + str(base_lower_price))
    print('limit_lower_price is ' + str(limit_lower_price))

    price_tick = math.log(1/data_df[['close']].iloc[-1] * 10e12, 1.0001)
    base_lower_tick = math.log(1/base_lower_price * 10e12, 1.0001)
    limit_lower_tick = math.log(1/limit_lower_price * 10e12, 1.0001)

    print('tick is ' + str(price_tick))
    print('base_lower_tick is ' + str(base_lower_tick))
    print('limit_lower_tick is ' + str(limit_lower_tick))
    base_width =  base_lower_tick - price_tick
    limit_width = limit_lower_tick - price_tick


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


def rebalance(limit_lower, base_lower, strategy, web3):
    print('Rebalancing')

    try:

        print('setBaseThreshold')
        nonce = web3.eth.getTransactionCount(keeper)
        tx = strategy.functions.setBaseThreshold(base_lower).buildTransaction(
        {
            'value': 0,
            'gas': 2000000,
            'chainId': 3,
            'nonce': nonce
        })
        signed_tx = web3.eth.account.sign_transaction(tx, private_key = pk)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)

        print('setLimitThreshold')
        nonce = web3.eth.getTransactionCount(keeper)
        tx = strategy.functions.setLimitThreshold(limit_lower).buildTransaction(
        {
            'value': 0,
            'gas': 2000000,
            'chainId': 3,
            'nonce': nonce
        })
        signed_tx = web3.eth.account.sign_transaction(tx, private_key = pk)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)

        print('rebalance tx')
        nonce = web3.eth.getTransactionCount(keeper)
        tx = strategy.functions.rebalance().buildTransaction(
        {
            'value': 0,
            'gas': 2000000,
            'chainId': 3,
            'nonce': nonce
        })
        signed_tx = web3.eth.account.sign_transaction(tx, private_key = pk)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)

        print('Rebalance successful')
    except Exception as e:
        print(e)
        print('Rebalance failed')
    return
    



def get_last_rebalance(cur):
    try:
        cur.execute("SELECT rebalance_timestamp FROM keeperbot_data WHERE rebalance_timestamp IS NOT NULL ORDER BY timestamp DESC LIMIT 1")
        last_rebalance = cur.fetchone()[0]

        last_rebalance = last_rebalance.replace(tzinfo=None)
    except Exception as e:
        print(e)
        last_rebalance = None

    return last_rebalance


fetch()