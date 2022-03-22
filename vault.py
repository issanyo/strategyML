import math
from brownie import Contract

from utils import get_contract_abi

abi = get_contract_abi()


def get_vault(vault_address):
    return Contract("AlphaVault", address=vault_address, abi=abi['AlphaVault'])


def get_tokens(vault):
    token0 = Contract("token0", address=vault.token0(), abi=abi['MockToken'])
    token1 = Contract("token1", address=vault.token1(), abi=abi['MockToken'])
    return [token0, token1]


def get_strategy(strategy_address):
    return Contract("YoStrategy", address=strategy_address, abi=abi['YoStrategy'])


def get_vault_data(vault, strategy, tokens):
    data = {}
    data['total0'], data['total1'] = vault.getTotalAmounts()
    data['total0'] *= (10 ** (-1 * tokens[0].decimals()))
    data['total1'] *= (10 ** (-1 * tokens[1].decimals()))

    data['baseLower'] = to_price(vault.baseLower(), tokens)
    data['baseUpper'] = to_price(vault.baseUpper(), tokens)
    data['limitLower'] = to_price(vault.limitLower(), tokens)
    data['limitUpper'] = to_price(vault.limitUpper(), tokens)

    data['total0_limit'], data['total1_limit'] = vault.getPositionAmounts(vault.limitLower(), vault.limitUpper())
    data['total0_base'], data['total1_base'] = vault.getPositionAmounts(vault.baseLower(), vault.baseUpper())

    #data['outstandingShares'] = vault.totalSupply()

    tick, price = get_tick_price(strategy, tokens)
    data['tick'] = tick
    data['price'] = price

    data['tvl'] = data['total0'] + data['price'] * data['total1']

    print(data)

    return data


def get_tick_price(strategy, tokens):
    tick = strategy.getTick()
    price = to_price(tick, tokens)

    return tick, price


def to_price(tick, tokens):
    decimal0 = tokens[0].decimals()
    decimal1 = tokens[1].decimals()

    return 1/((1.0001 ** tick) * (10 ** (-1 * abs(decimal0 - decimal1))))


def calculate_tick_for_range(range, strategy, tokens):
    tick, price = get_tick_price(strategy, tokens)
    tick_with_range = to_tick(price + range, tokens)

    diff = abs(tick - tick_with_range)
    normalized_diff = normalize_tick(diff, strategy)

    print("range", range, "tick", diff, "tick_normalized", normalized_diff)
    return normalized_diff


def to_tick(price, tokens):
    decimal0 = tokens[0].decimals()
    decimal1 = tokens[1].decimals()

    tick = math.log(1 / price / (10 ** (-1 * abs(decimal0 - decimal1))), 1.0001)

    return int(tick)


def normalize_tick(tick, strategy):
    tick_spacing = strategy.tickSpacing()
    return int(math.ceil(tick / tick_spacing)) * tick_spacing
