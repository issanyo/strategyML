from brownie import accounts
from brownie.network import priority_fee, gas_price, gas_limit
from brownie.network.gas.strategies import ExponentialScalingStrategy

from vault import to_tick, getSqrtRatioAtTick


def rebalance(strategy, base, limit, swapAmount, sqrtPriceLimitX96, pk, legacy_gas=False):

    accounts.add(pk)
    deployer = accounts[-1]
    print("deployer", deployer, "balance: ", deployer.balance())

    if legacy_gas:
        gas_price(ExponentialScalingStrategy("2 gwei", "10 gwei"))
    else:
        priority_fee("auto")
    gas_limit("auto")

    print("Rebalancing with base:", base, "limit:", limit, "swapAmount:", swapAmount, "sqrtPriceLimitX96:", sqrtPriceLimitX96)
    return strategy.rebalance(base, limit, swapAmount, sqrtPriceLimitX96, {'from': deployer})


def calculate_amounts_to_rebalance(vault_data, tokens):
    half_tvl = vault_data['tvl'] / 2  # 200 -> 100

    # if 75% of funds are already balanced, do not perform swaps
    TOKEN0_THRESHOLD = half_tvl * 0.25
    TOKEN1_THRESHOLD = half_tvl * 0.25 / vault_data['price']
    SLIPPAGE = 10

    token0q = vault_data['total0'] - half_tvl
    token1q = vault_data['total1'] - half_tvl / vault_data['price']
    # 0, 200 -> -100, 100
    # 100, 100 -> 0, 0
    # 200, 0 -> 100, -100
    # 50, 150 -> -50, 50
    # 150, 50 -> 50, -50

    # sell
    amountToSwap = 0
    sqrtPriceLimitX96 = 0
    if token1q > 0 and token1q > TOKEN1_THRESHOLD:
        # from token1 to token0 (negative)
        amountToSwap = - token1q * (10 ** tokens[1].decimals())
        sqrtPriceLimitX96 = getSqrtRatioAtTick(to_tick(vault_data['price'] + SLIPPAGE, tokens))
    # buy
    elif token0q > 0 and token0q > TOKEN0_THRESHOLD:
        # from token0 to token1 (positive)
        amountToSwap = token0q * (10 ** tokens[0].decimals())
        sqrtPriceLimitX96 = getSqrtRatioAtTick(to_tick(vault_data['price'] - SLIPPAGE, tokens))

    return [amountToSwap, sqrtPriceLimitX96]
