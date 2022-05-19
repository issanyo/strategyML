import numpy as np
import tensorflow as tf

# Disable AutoShard.
options = tf.data.Options()
options.experimental_distribute.auto_shard_policy = tf.data.experimental.AutoShardPolicy.OFF #AutoShardPolicy.DATA
LOOKBACK = 6

def load_model(vault_address):
    global LOOKBACK
    LOOKBACK = 6
    if vault_address == "0x1B94C4EC191Cc4D795Cd0f0929C59cA733b6E636": # ETH/USDC
        return tf.keras.models.load_model('./ml/dataset_update_agent_pooling_x2')

    LOOKBACK = 12
    return tf.keras.models.load_model('./ml/btc_inverted_x2_lookback_12_full')

def predict(model, state):
    state = tf.data.Dataset.from_tensors(state)
    state = state.with_options(options)

    action_probs = model.predict(state.batch(LOOKBACK))

    action = np.argmax(action_probs[0])
    print("prediction results ", action_probs, "choosing action ", action)

    return action
