from pandas.core import base
from web3 import Web3, middleware
from web3.gas_strategies.time_based import medium_gas_price_strategy

from datetime import datetime, timedelta
import os
from utils import get_contract_abi, connect_db
from vault import get_vault_data
from the_graph_data import fetch_thegraph_data
from strategy import rebalance
from config import infura, vaults
from db import insert_data

keeper = os.environ['KEEPER']
pk = os.environ['PK']
WEB3_INFURA_PROJECT_ID = os.environ['WEB3_INFURA_PROJECT_ID']


def fetch(network):
    abi = get_contract_abi()
    con = connect_db()

    web3 = Web3(Web3.HTTPProvider(infura[network]))
    web3.eth.set_gas_price_strategy(medium_gas_price_strategy)

    web3.middleware_onion.add(middleware.time_based_cache_middleware)
    web3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
    web3.middleware_onion.add(middleware.simple_cache_middleware)
    for (vault_address) in vaults[network]:
        vault = web3.eth.contract(vault_address, abi=abi['AlphaVault'])
        strategy = web3.eth.contract(vault.functions.strategy().call(), abi=abi['DynamicRangesStrategy'])

        theGraphData = fetch_thegraph_data(strategy)

        cur = con.cursor()

        last_rebalance = get_last_rebalance(cur, network)
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

        vault_data = get_vault_data(vault, strategy, web3, abi)

        insert_data(cur, con, vault_data, theGraphData, timestamp, last_rebalance, rebalance_check, network)

        con.close()


def get_last_rebalance(cur, network):
    try:
        print("SELECT rebalance_timestamp FROM keeperbot_data WHERE rebalance_timestamp IS NOT NULL AND network = '" + network + "'  ORDER BY timestamp DESC LIMIT 1")
        cur.execute("SELECT rebalance_timestamp FROM keeperbot_data WHERE rebalance_timestamp IS NOT NULL AND network = '" + network + "'  ORDER BY timestamp DESC LIMIT 1")
        last_rebalance = cur.fetchone()[0]

        last_rebalance = last_rebalance.replace(tzinfo=None)
    except Exception as e:
        print(e)
        last_rebalance = None

    return last_rebalance


fetch('ropsten')