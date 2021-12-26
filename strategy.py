from utils import get_contract_abi, connect_db
from vault import get_vault_data
from the_graph_data import fetch_thegraph_data
from config import vaults
from db import insert_data
from pandas.core import base
from web3 import Web3, middleware
from web3.gas_strategies.time_based import fast_gas_price_strategy
from datetime import datetime, timedelta

TIMEOUT_WAIT_TRANSACTION = 3600*2 #2 hours max wait for transaction
TRANSACTION_POLL_LATENCY = 10

def get_nonce(ethereum_account_address, web3):
    return web3.eth.getTransactionCount(ethereum_account_address) + 1


def rebalance(limit_lower, base_lower, strategy, web3, keeper, pk):
    print('Rebalancing...')

    estimation = strategy.functions.setBaseThreshold(base_lower).estimateGas({'from': keeper})
    print('setBaseThreshold, gas estimate: ', estimation)

    tx = strategy.functions.setBaseThreshold(base_lower).buildTransaction(
    {
        'value': 0,
        'from': keeper,
        'nonce': get_nonce(keeper, web3),
        'gas': estimation
    })

    signed_tx = web3.eth.account.sign_transaction(tx, private_key = pk)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=TIMEOUT_WAIT_TRANSACTION, poll_latency=TRANSACTION_POLL_LATENCY)

    estimation = strategy.functions.setLimitThreshold(limit_lower).estimateGas({'from': keeper})
    print('setLimitThreshold, gas estimate: ', estimation)

    tx = strategy.functions.setLimitThreshold(limit_lower).buildTransaction(
    {
        'value': 0,
        'from': keeper,
        'nonce': get_nonce(keeper, web3),
        'gas': estimation
    })
    signed_tx = web3.eth.account.sign_transaction(tx, private_key = pk)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=TIMEOUT_WAIT_TRANSACTION, poll_latency=TRANSACTION_POLL_LATENCY)

    estimation = strategy.functions.rebalance().estimateGas({'from': keeper})
    print('Rebalance, gas estimate: ', estimation)

    tx = strategy.functions.rebalance().buildTransaction(
    {
        'value': 0,
        'from': keeper,
        'nonce': get_nonce(keeper, web3),
        'gas': estimation
    })
    signed_tx = web3.eth.account.sign_transaction(tx, private_key = pk)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=TIMEOUT_WAIT_TRANSACTION, poll_latency=TRANSACTION_POLL_LATENCY)

    print('Rebalance successful, transaction: ', tx_receipt)


def fetch_and_rebalance(network, infura_url, keeper, pk):
    abi = get_contract_abi()
    con = connect_db()

    web3 = Web3(Web3.HTTPProvider(infura_url))
    web3.eth.set_gas_price_strategy(fast_gas_price_strategy)

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

        rebalance_check = False
        if timestamp - last_rebalance > timedelta(hours=48) or True:
            rebalance(theGraphData['limit_lower'], theGraphData['base_lower'], strategy, web3, keeper, pk)
            last_rebalance = timestamp
            rebalance_check = True

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
