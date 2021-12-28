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
    Contract
)
from brownie.network import priority_fee, gas_price, gas_limit
from brownie.network.gas.strategies import ExponentialScalingStrategy

def rebalance(limit_lower, base_lower, strategy, keeper, pk, legacyGasPrice = True):
    print('Rebalancing...')

    print('setBaseThreshold')
    strategy.setBaseThreshold(base_lower, {'from': keeper})

    print('setBaseThreshold')
    strategy.setLimitThreshold(limit_lower, {'from': keeper})

    print('rebalance')
    strategy.rebalance({'from': keeper})

    print('Rebalance Done')


def fetch_and_rebalance(network, keeper, pk, legacy_gas=False):
    abi = get_contract_abi()
    con = connect_db()

    accounts.add(pk)
    deployer = accounts[0]
    print("deployer balance: ", deployer.balance())

    if legacy_gas:
        gas_price(ExponentialScalingStrategy("1 gwei", "2 gwei"))
    else:
        priority_fee("auto")
    gas_limit("auto")

    for (vault_address) in vaults[network]:
        vault = Contract("OrbitVault", address=vault_address, abi=abi['AlphaVault'])
        strategy = Contract("DynamicRangesStrategy", address=vault.strategy(), abi=abi['DynamicRangesStrategy'])

        theGraphData = fetch_thegraph_data(strategy)

        cur = con.cursor()

        last_rebalance = get_last_rebalance(cur, network)
        print("Last rebalance: ", last_rebalance)
        if not last_rebalance:
            last_rebalance = datetime.now()
        timestamp = datetime.now()

        rebalance_check = False
        if timestamp - last_rebalance > timedelta(hours=40):
            rebalance(theGraphData['limit_lower'], theGraphData['base_lower'], strategy, keeper, pk)
            last_rebalance = timestamp
            rebalance_check = True

        vault_data = get_vault_data(vault, strategy, abi)

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
