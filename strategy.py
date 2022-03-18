from brownie import accounts
from brownie.network import priority_fee, gas_price, gas_limit
from brownie.network.gas.strategies import ExponentialScalingStrategy

def rebalance(strategy, base, limit, pk, legacy_gas=False):

    accounts.add(pk)
    deployer = accounts[-1]
    print("deployer", deployer, "balance: ", deployer.balance())

    if legacy_gas:
        gas_price(ExponentialScalingStrategy("2 gwei", "10 gwei"))
    else:
        priority_fee("auto")
    gas_limit("auto")

    print("Rebalancing with base:", base, "limit:", limit)
    return strategy.rebalance(base, limit, {'from': deployer})
