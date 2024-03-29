import os

from db import insert_data, get_state, INVESTMENT
from ml.env import PriceEnv
from ml.env_btc import PriceEnv as PriceEnvBTC
from ml.model import load_model, predict
from vault import get_vault_data, get_vault, get_strategy, get_tokens, get_tick_price, calculate_tick_for_range
from strategy import rebalance, calculate_amounts_to_rebalance
from brownie import network
import numpy as np


def main(vault_address, strategy_address, network_, legacy_gas):
    network.connect(network_)

    model, lookback = load_model(vault_address)
    vault = get_vault(vault_address)
    strategy = get_strategy(strategy_address)
    tokens = get_tokens(vault)
    curr_vault_data = get_vault_data(vault, strategy, tokens)
    #last_predicted_action = get_config("future_action", vault_address) or 0

    env = PriceEnv([1]) if vault_address == "0x1B94C4EC191Cc4D795Cd0f0929C59cA733b6E636" else PriceEnvBTC([1])
    env.seed(0)
    state, last_action = get_state(vault_address, lookback, env)

    # Update environment with latest data
    tick, price = get_tick_price(strategy, tokens)
    #env.reset_status_and_price(price, [curr_vault_data['total0'], curr_vault_data['total1']], env.current_action_range_val(), env.prepare_bounds_for_env(curr_vault_data), INVESTMENT[vault_address])

    print("state:", state)
    predicted_action = 0
    if len(state) == lookback and last_action == 0: # do not perform 2 consecutive actions (to update the state)
        predicted_action = predict(model, state)
        if isinstance(predicted_action, np.generic):
            predicted_action = predicted_action.item()

    if env.current_action_range == 1 and predicted_action == 2: # no decrement to zero
        predicted_action = 3

    env.add_price(price) # just to move forward
    new_state, reward, done, _ = env.step(predicted_action)

    # 0.016
    collectFees = []
    gas_used = 0
    if False: #predicted_action != 0:
        #new_range = env.current_action_range_converted()
        new_range = 0.01
        print("current range:", env.current_action_range_val(), "converted:", new_range)
        base = calculate_tick_for_range(new_range, strategy, tokens)
        limit = calculate_tick_for_range(new_range, strategy, tokens)
        swapAmount, sqrtPriceLimitX96 = calculate_amounts_to_rebalance(vault_address, curr_vault_data, tokens)

        tx = rebalance(strategy, base, limit, swapAmount, sqrtPriceLimitX96, os.environ['STRATEGY_PK'], legacy_gas)

        gas_used = np.round(tx.gas_used * tx.priority_fee * 1e-18, 9).item()# gas in Matic
        #print(tx.info())
        collectFees = [
            {"feesToVault0": tx.events["CollectFees"][0]["feesToVault0"], "feesToVault1": tx.events["CollectFees"][0]["feesToVault1"]},
            {"feesToVault0": tx.events["CollectFees"][1]["feesToVault0"], "feesToVault1": tx.events["CollectFees"][1]["feesToVault1"]}
        ]

        print("collectFees: ", collectFees)
        print("Snapshot: ", tx.events["Snapshot"][0])

    vault_data = get_vault_data(vault, strategy, tokens)

    insert_data(vault_address, vault_data, env.current_action_range_val(), predicted_action, new_state, reward, collectFees, gas_used, network_, tokens)

    network.disconnect()
