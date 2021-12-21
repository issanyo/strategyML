from pandas.core import base
from web3 import Web3, middleware
from web3.gas_strategies.time_based import medium_gas_price_strategy

from datetime import datetime, timedelta
import os
import psycopg2
from utils import get_contract_abi, connect_db
from vault import get_vault_data
from the_graph_data import fetch_thegraph_data
from strategy import rebalance

keeper = '0xffa9FDa3050007645945e38E72B5a3dB1414A59b'
pk = os.environ['PK']
WEB3_INFURA_PROJECT_ID = os.environ['WEB3_INFURA_PROJECT_ID']


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
        if timestamp - last_rebalance < timedelta(hours=48):
            rebalance(theGraphData['limit_lower'], theGraphData['base_lower'], strategy, web3)
            last_rebalance = timestamp
            rebalance_check = True
        else:
            rebalance_check = False
    except Exception as e:
        print(e)

    vault_data = get_vault_data(vault, strategy, web3, abi)

    
    try:
        cur.execute("INSERT INTO keeperbot_data (token0_quantity, token1_quantity, \"baseLower\", \"baseUpper\", \"limitUpper\", \"limitLower\", \"totalSupply\", \"priceStrategy\", tvl, pool_address, strategy_address, timestamp, price_graph, volume, liquidity, fees_pool, rebalance_check, rebalance_timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (vault_data['total0'], vault_data['total1'], vault_data['baseLower'], vault_data['baseUpper'], vault_data['limitUpper'], vault_data['limitLower'], vault_data['outstandingShares'], vault_data['price'], vault_data['tvl'], '0x624633fD2Eff00cBFC7294CABD80303b12C5fD9d', '0x4Bb99cfEe541C66a79D4DaeB4431BCfe8de1d410', timestamp, theGraphData['priceGraph'], theGraphData['volume'], theGraphData['liquidity'], theGraphData['fees_pool'], rebalance_check, last_rebalance))
        con.commit()
        print('Data successfully inserted')
    except psycopg2.Error as e:
        print(e)
        con.rollback()

    con.close()


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