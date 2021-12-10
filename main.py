from web3 import Web3

import binascii
import requests
from datetime import datetime
import json
import numpy as np
from utils import getContractAbi, connectDB
import os
import psycopg2
import pandas as pd
import numpy as np
import matplotlib


def test_transaction():
    pk = '6000e057971f9f094145f7f5a088b6a277eb904ec77288ec873aedca9fafcb7f'
    WEB3_INFURA_KEY = 'cf01a35558ad4215aebc2042577b2f23'
    web3 = Web3(Web3.HTTPProvider('https://ropsten.infura.io/v3/' + WEB3_INFURA_KEY))
    balance = web3.eth.get_balance('0xffa9FDa3050007645945e38E72B5a3dB1414A59b')

    print(balance)
    receiverAccount = '0xaaB5a17c0d9d09632F013d8b5E2353A77710dDc1'
    keeper = '0xffa9FDa3050007645945e38E72B5a3dB1414A59b'

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
    WEB3_INFURA_KEY = 'cf01a35558ad4215aebc2042577b2f23'
    abi = getContractAbi()
    con = connectDB()
    theGraphData = fetch_thegraph_data()


    web3 = Web3(Web3.HTTPProvider('https://ropsten.infura.io/v3/' + WEB3_INFURA_KEY))
    vault = web3.eth.contract('0x624633fD2Eff00cBFC7294CABD80303b12C5fD9d', abi=abi['AlphaVault'])
    strategy = web3.eth.contract('0x4Bb99cfEe541C66a79D4DaeB4431BCfe8de1d410', abi=abi['DynamicRangesStrategy'])

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
    timestamp = datetime.now()

    print('total0: ' + str(total0) + '\n' + 'total1: ' + str(total1) + '\n' + 'baseLower is ' + str(baseLower) + '\n' + 'baseUpper is ' + str(baseUpper) + '\n' + 'limitUpper is ' + str(limitUpper) + '\n' + 'limitLower is ' + str(limitLower) + '\n' + 'outstanding shares is ' + str(outstandingShares) + '\n' + 'tick is ' + str(tick) + '\n' + 'price is ' + str(price) + '\n' + 'tvl is ' + str(tvl) + '\n')

    cur = con.cursor()
    
    try:
        cur.execute("INSERT INTO keeperbot_data (token0_quantity, token1_quantity, \"baseLower\", \"baseUpper\", \"limitUpper\", \"limitLower\", \"totalSupply\", \"priceStrategy\", tvl, pool_address, strategy_address, timestamp, price_graph, volume, liquidity, fees_pool) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (total0, total1, baseLower, baseUpper, limitUpper, limitLower, outstandingShares, price, tvl, '0x624633fD2Eff00cBFC7294CABD80303b12C5fD9d', '0x4Bb99cfEe541C66a79D4DaeB4431BCfe8de1d410', timestamp, theGraphData['priceGraph'], theGraphData['volume'], theGraphData['liquidity'], theGraphData['fees_pool']))
        con.commit()
        print('Data successfully inserted')
    except psycopg2.Error as e:
        print(e)
        con.rollback()


    con.close()


#fetch()



"""

    Fetching historical data from the graph

    0xCBCdF9626bC03E24f779434178A73a0B4bad62eD

    as the bitcoin / eth address

"""

def fetch_thegraph_data():

    pool_starting_date = "2021-05-04 00:00:00"

    starting_pool = datetime.fromisoformat(pool_starting_date)
    days_timedelta = datetime.today() - starting_pool
    days = days_timedelta.days
    print(days)

    query = """
            {
                pool(id: "0xcbcdf9626bc03e24f779434178a73a0b4bad62ed")
                    {
                    poolDayData (first : """+ str(days) + """) {
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
    request = requests.post('https://gateway.thegraph.com/api/6de22021c61c1ccc2002599b5750c305/subgraphs/id/0x9bde7bf4d5b13ef94373ced7c8ee0be59735a298-2'
                                    '', json={'query': query})


    data_dct = request.json()['data']['pool']['poolDayData']

    data_df = pd.DataFrame(data_dct)
    print(data_df.tail(1))


    data_df["date"] = pd.to_datetime(data_df["date"], unit = "s")

    data_df[[col for col in data_df.columns if col not in ("date","id")]] = data_df[[col for col in data_df.columns if col not in ("date","id")]].astype(float)

    data_df[["pct_change_close"]] = data_df[["close"]].pct_change(periods = 1)

    data_df.replace([np.inf, -np.inf], np.nan, inplace=True)

    data_df[["pct_change_close"]].hist()
    lastRow = data_df.iloc[-1]

    print(lastRow['close'])
 

    finalDataDict = {
        'priceGraph': lastRow['close'],
        'volume': lastRow['volumeUSD'],
        'liquidity': lastRow['liquidity'],
        'fees_pool': lastRow['feesUSD'],
    }

    return finalDataDict

fetch()