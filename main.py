import os

from db import insert_data, get_state
from ml.env import PriceEnv
from ml.model import load_model, LOOKBACK, predict
from vault import get_vault_data, get_vault, get_strategy, get_tokens, get_tick_price, calculate_tick_for_range
from strategy import rebalance
from brownie import network
import numpy

def main():
    model = load_model()
    vault = get_vault("0x34b97ffa01dc0DC959c5f1176273D0de3be914C1")
    strategy = get_strategy("0x741e3E1f81041c62C2A97d0b6E567AcaB09A6232")
    tokens = get_tokens(vault)

    env = PriceEnv([0])
    env.seed(0)
    state = get_state(LOOKBACK, env)
    print("state:", state)

    tick, price = get_tick_price(strategy, tokens)
    env.add_price(int(price))

    predicted_action = 0
    if len(state) == LOOKBACK:
        predicted_action = predict(model, state)
        if isinstance(predicted_action, numpy.generic):
            predicted_action = predicted_action.item()

    new_state, reward, done, _ = env.step(predicted_action)

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

    insert_data(vault_data, env, predicted_action, reward, collectFees, gas_used)


network.connect('development')
main()
network.disconnect()
