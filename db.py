from pymongo import MongoClient
from datetime import timedelta, datetime

from ml.env import PriceEnv


def get_db():
    client = MongoClient()
    return client.uniswap


def insert_data(vault_data, env: PriceEnv, action: int, reward_env, collectFees, gas_used, network="polygon"):
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
            "reward": reward_env
        },
        "network": network,
        "datetime": datetime.utcnow()
    }
    strategy_ = db["strategy"]
    result = strategy_.insert_one(data)
    print("data inserted on db")
    return result


def get_state(lookback, env):
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
