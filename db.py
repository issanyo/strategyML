import math

from pymongo import MongoClient
from datetime import timedelta, datetime
import psycopg2
from ml.env import PriceEnv
from psycopg2.extensions import AsIs
import os

from vault import calculate_tvl

INVESTMENT = {"0x1B94C4EC191Cc4D795Cd0f0929C59cA733b6E636": [100, 0.035],
              "0x11631E3B97Ea45189985ae45FFC9FD49621776b1": [0.0016, 0.02]}

def get_db():
    client = MongoClient()
    return client.uniswap


def insert_data(vault, vault_data, range: int, action: int, new_state, reward_env, collectFees, gas_used, network, tokens):
    db = get_db()
    data = {
        "vault": {
            "token0_quantity": vault_data['total0'],
            "token1_quantity": vault_data['total1'],
            "baseLower": vault_data['baseLower'],
            "baseUpper": vault_data['baseUpper'],
            "limitLower": vault_data['limitLower'],
            "limitUpper": vault_data['limitUpper'],
            "tick": vault_data['tick'],
            "price": vault_data['price'],
            "tvl": vault_data['tvl'],
            "gas_used": gas_used,
            "collectFees": collectFees,
            "total0_limit": vault_data['total0_limit'],
            "total1_limit": vault_data['total1_limit'],
            "total0_base": vault_data['total0_base'],
            "total1_base": vault_data['total1_base'],
        },
        "env": {
            "range": range,
            "action": action,
            "reward": reward_env,
            "state": new_state
        },
        "network": network,
        "datetime": datetime.utcnow(),
        "vault_address": vault
    }
    strategy_ = db["strategy"]
    result = strategy_.insert_one(data)

    postgress_data = {
        "token0_quantity": vault_data['total0'],
        "token1_quantity": vault_data['total1'],
        "baseLower": vault_data['baseLower'],
        "baseUpper": vault_data['baseUpper'],
        "limitLower": vault_data['limitLower'],
        "limitUpper": vault_data['limitUpper'],
        "price": vault_data['price'],
        "tvl": vault_data['tvl'],
        "gas_used": gas_used,
        "datetime": data["datetime"],
        "tvl_holding": INVESTMENT[vault][0] + INVESTMENT[vault][1] * vault_data['price'],
        "vault_address": vault
    }
    if len(collectFees) > 0:
        postgress_data["collectFeesBase"] = calculate_tvl(collectFees[0]["feesToVault0"], collectFees[0]["feesToVault1"], vault_data['price'], tokens)
    if len(collectFees) > 1:
        postgress_data["collectFeesLimit"] = calculate_tvl(collectFees[1]["feesToVault0"], collectFees[1]["feesToVault1"], vault_data['price'], tokens)

    insert_data_postgress(postgress_data)

    print("data inserted on db")
    return result


def get_state(vault, lookback, env: PriceEnv):
    from_date = datetime.utcnow() - timedelta(hours=lookback*2)

    db = get_db()
    state = []
    counter = 0
    for data in db["strategy"].find({'vault_address': vault, 'datetime': {"$gte": from_date}}).sort('datetime', 1):
        if counter > 0:
            env.add_price(data["vault"]["price"])
            curr_state, reward, done, _ = env.step(data["env"]["action"], env.prepare_bounds_for_env(data["vault"]))
            state.append(curr_state)
            #print("[get_state] action:", data["env"]["action"], "state:", curr_state)

        #print("[get_state] mongo data:", data)
        env.reset_status_and_price(data["vault"]["price"], [data["vault"]["token0_quantity"], data["vault"]["token1_quantity"]], data["env"]["range"], env.prepare_bounds_for_env(data["vault"]), INVESTMENT[vault])

        counter += 1

    return state[-lookback:]


def get_config(name, vault):
    db = get_db()
    strategy_temp_data = db["strategy_config"]
    config = strategy_temp_data.find_one({"name": name, "vault": vault})
    return config["value"] if config else None


def insert_data_postgress(data):
    user = os.environ['DB_USER']
    pwd = os.environ['DB_PASS']
    con = psycopg2.connect("dbname='uniswap' user='" + user + "' host='localhost' password='" + pwd + "'")
    cur = con.cursor()

    insert_statement = 'insert into strategy (%s) values %s'
    columns = data.keys()
    values = [data[column] for column in columns]

    try:
        cur.execute(insert_statement, (AsIs(','.join(columns)), tuple(values)))
        con.commit()
    except psycopg2.Error as e:
        print(e)
        con.rollback()

    con.close()
