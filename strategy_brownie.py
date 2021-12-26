from .utils import get_contract_abi, connect_db
from .vault import get_vault_data
from .the_graph_data import fetch_thegraph_data
from .config import vaults
from .db import insert_data
from datetime import datetime, timedelta
from brownie import (
    accounts,
    project,
    #OrbitVault,
    #DynamicRangesStrategy,
    Contract,
    interface
)
from brownie.network import priority_fee, gas_price, gas_limit

def rebalance(limit_lower, base_lower, strategy, web3, keeper, pk, legacyGasPrice = True):
    print('Rebalancing...')

    estimation = strategy.functions.setBaseThreshold(base_lower).estimateGas({'from': keeper})
    priority = get_max_priority_fee(web3)
    print('setBaseThreshold, gas estimate: ', estimation)
    print("eth gas price: ", web3.eth.gas_price )

    # Dynamic fee transaction, introduced by EIP-1559
    transaction_data = {
        'value': 0,
        'from': keeper,
        'nonce': get_nonce(keeper, web3),
        'chainId': 3,
    }
    if legacyGasPrice:
        transaction_data["gasPrice"]= int(web3.eth.gas_price * 1.40)
    else:
        transaction_data["maxFeePerGas"] = (priority + estimation) * 2,
        transaction_data["maxPriorityFeePerGas"] = priority + estimation

    tx = strategy.functions.setBaseThreshold(base_lower).buildTransaction(transaction_data)

    signed_tx = web3.eth.account.sign_transaction(tx, private_key = pk)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=TIMEOUT_WAIT_TRANSACTION, poll_latency=TRANSACTION_POLL_LATENCY)

    estimation = strategy.functions.setLimitThreshold(limit_lower).estimateGas({'from': keeper})
    priority = get_max_priority_fee(web3)
    print('setLimitThreshold, gas estimate: ', estimation)

    transaction_data = {
        'value': 0,
        'from': keeper,
        'nonce': get_nonce(keeper, web3),
        'chainId': 3,
    }
    if legacyGasPrice:
        transaction_data["gasPrice"] = int(web3.eth.gas_price * 1.40)
    else:
        transaction_data["maxFeePerGas"] = (priority + estimation) * 2,
        transaction_data["maxPriorityFeePerGas"] = priority + estimation

    tx = strategy.functions.setLimitThreshold(limit_lower).buildTransaction(transaction_data)
    signed_tx = web3.eth.account.sign_transaction(tx, private_key = pk)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=TIMEOUT_WAIT_TRANSACTION, poll_latency=TRANSACTION_POLL_LATENCY)

    estimation = strategy.functions.rebalance().estimateGas({'from': keeper})
    priority = get_max_priority_fee(web3)
    print('Rebalance, gas estimate: ', estimation)

    transaction_data = {
        'value': 0,
        'from': keeper,
        'nonce': get_nonce(keeper, web3),
        'chainId': 3,
    }
    if legacyGasPrice:
        transaction_data["gasPrice"] = int(web3.eth.gas_price * 1.40)
    else:
        transaction_data["maxFeePerGas"] = (priority + estimation) * 2,
        transaction_data["maxPriorityFeePerGas"] = priority + estimation

    tx = strategy.functions.rebalance().buildTransaction(transaction_data)
    signed_tx = web3.eth.account.sign_transaction(tx, private_key = pk)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=TIMEOUT_WAIT_TRANSACTION, poll_latency=TRANSACTION_POLL_LATENCY)

    print('Rebalance successful, transaction: ', tx_receipt)


def fetch_and_rebalance(network, keeper, pk):
    abi = get_contract_abi()
    con = connect_db()

    accounts.add(pk)
    deployer = accounts[0]
    print("deployer balance: ", deployer.balance())

    priority_fee("auto")
    gas_limit("auto")

    for (vault_address) in vaults[network]:
        vault = Contract(vault_address, abi=abi['AlphaVault'])
        strategy = Contract(vault.strategy(), abi=abi['DynamicRangesStrategy'])

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
fetch_and_rebalance("ropsten", "0x66aB6D9362d4F35596279692F0251Db635165871", "bbfbee4961061d506ffbb11dfea64eba16355cbf1d9c29613126ba7fec0aed5d")
