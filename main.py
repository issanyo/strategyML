import os

from db import insert_data, get_state, get_config
from ml.env import PriceEnv
from ml.model import load_model, LOOKBACK, predict
from vault import get_vault_data, get_vault, get_strategy, get_tokens, get_tick_price, calculate_tick_for_range
from strategy import rebalance
from brownie import network
import numpy as np

def main():
    model = load_model()
    vault = get_vault("0x34b97ffa01dc0DC959c5f1176273D0de3be914C1")
    strategy = get_strategy("0x741e3E1f81041c62C2A97d0b6E567AcaB09A6232")
    tokens = get_tokens(vault)
    curr_vault_data = get_vault_data(vault, strategy, tokens)
    last_predicted_action = get_config("future_action") or 0

    env = PriceEnv([0])
    env.seed(0)
    state = get_state(LOOKBACK-1, env)

    # Update environment with latest data
    tick, price = get_tick_price(strategy, tokens)
    env.add_price(int(price))
    env.il = [curr_vault_data["total0"], curr_vault_data["total1"]]
    env.assets_price = curr_vault_data["tvl"]

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
        limit = calculate_tick_for_range(env.current_action_range_val() * 0.75, strategy, tokens)

        tx = rebalance(strategy, base, limit, os.environ['STRATEGY_PK'], True) # TODO: remove legacy gas

        gas_used = tx.gas_used
        #print(tx.info())
        collectFees = [
            {"feesToVault0": tx.events["CollectFees"][0]["feesToVault0"], "feesToVault1": tx.events["CollectFees"][0]["feesToVault1"]},
            {"feesToVault0": tx.events["CollectFees"][1]["feesToVault0"], "feesToVault1": tx.events["CollectFees"][1]["feesToVault1"]}
        ]

        print("collectFees: ", collectFees)
        print("Snapshot: ", tx.events["Snapshot"][0])

    vault_data = get_vault_data(vault, strategy, tokens)

    insert_data(vault_data, env, last_predicted_action, predicted_action, new_state, reward, collectFees, gas_used)


network.connect('development')
main()
network.disconnect()
