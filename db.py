from pymongo import MongoClient
from datetime import timedelta, datetime
import psycopg2
from ml.env import PriceEnv
from psycopg2.extensions import AsIs
import os

def get_db():
    client = MongoClient()
    return client.uniswap


def insert_data(vault_data, env: PriceEnv, action: int, future_action: int, new_state, reward_env, collectFees, gas_used, network):
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
            "collectFees": collectFees
        },
        "env": {
            "range": env.current_action_range_val(),
            "action": action,
            "reward": reward_env,
            "state": new_state
        },
        "network": network,
        "datetime": datetime.utcnow()
    }
    strategy_ = db["strategy"]
    result = strategy_.insert_one(data)

    strategy_temp_data = db["strategy_config"]
    strategy_temp_data.update_one({"name": "future_action"},
                                  {"$set": {"value": future_action, "name": "future_action", "datetime": datetime.utcnow()}},
                                  upsert=True)

    postgress_data = data["vault"]
    del postgress_data["collectFees"]
    del postgress_data["tick"]
    postgress_data["datetime"] = data["datetime"]
    postgress_data["tvl_holding"] = 100 + 0.035 * postgress_data['price']
    insert_data_postgress(postgress_data)

    print("data inserted on db")
    return result


def get_state(lookback, env: PriceEnv):
    from_date = datetime.utcnow() - timedelta(hours=lookback*2)

    db = get_db()
    state = []
    counter = 0
    for data in db["strategy"].find({'datetime': {"$gte": from_date}}).sort('datetime', 1):
        if counter > 0:
            env.add_price(int(data["vault"]["price"]))
            curr_state, reward, done, _ = env.step(data["env"]["action"])
            state.append(curr_state)

        env.reset_status_and_price(int(data["vault"]["price"]), [data["vault"]["token0_quantity"], data["vault"]["token1_quantity"]], data["env"]["range"])

        counter += 1

    return state[-lookback:]


def get_config(name):
    db = get_db()
    strategy_temp_data = db["strategy_config"]
    config = strategy_temp_data.find_one({"name": name})
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
