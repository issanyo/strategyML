import os

from db import insert_data, get_state, get_config
from ml.env import PriceEnv
from ml.model import load_model, LOOKBACK, predict
from vault import get_vault_data, get_vault, get_strategy, get_tokens, get_tick_price, calculate_tick_for_range
from strategy import rebalance
from brownie import network
import numpy as np


def main(vault_address, strategy_address, network_, legacy_gas):
    network.connect(network_)

    model = load_model()
    vault = get_vault(vault_address)
    strategy = get_strategy(strategy_address)
    tokens = get_tokens(vault)
    curr_vault_data = get_vault_data(vault, strategy, tokens)
    last_predicted_action = get_config("future_action") or 0

    env = PriceEnv([0])
    env.seed(0)
    state = get_state(LOOKBACK-1, env)

    # Update environment with latest data
    tick, price = get_tick_price(strategy, tokens)
    env.add_price(int(price))

    new_state, reward, done, _ = env.step(last_predicted_action)
    state.append(new_state)

    print("state:", state)
    predicted_action = 0
    if len(state) == LOOKBACK:
        predicted_action = predict(model, state)
        if isinstance(predicted_action, np.generic):
            predicted_action = predicted_action.item()

    collectFees = []
    gas_used = 0
    if predicted_action != 0:
        base = calculate_tick_for_range(env.current_action_range_val(), strategy, tokens)
        limit = calculate_tick_for_range(env.current_action_range_val() * 2, strategy, tokens)

        tx = rebalance(strategy, base, limit, os.environ['STRATEGY_PK'], legacy_gas)

        gas_used = np.round(tx.gas_used * tx.priority_fee * 1e-18, 9).item()# gas in Matic
        #print(tx.info())
        collectFees = [
            {"feesToVault0": tx.events["CollectFees"][0]["feesToVault0"], "feesToVault1": tx.events["CollectFees"][0]["feesToVault1"]},
            {"feesToVault0": tx.events["CollectFees"][1]["feesToVault0"], "feesToVault1": tx.events["CollectFees"][1]["feesToVault1"]}
        ]

        print("collectFees: ", collectFees)
        print("Snapshot: ", tx.events["Snapshot"][0])

    vault_data = get_vault_data(vault, strategy, tokens)

    insert_data(vault_data, env, last_predicted_action, predicted_action, new_state, reward, collectFees, gas_used, network_, tokens)

    network.disconnect()
