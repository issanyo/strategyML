import numpy as np
import tensorflow as tf
from ml.custom_strategy import SimpleStrategy

options = tf.data.Options()
options.experimental_distribute.auto_shard_policy = tf.data.experimental.AutoShardPolicy.OFF #AutoShardPolicy.DATA

def load_model(vault_address):
    lookback = 6
    if vault_address == "0x1B94C4EC191Cc4D795Cd0f0929C59cA733b6E636": # ETH/USDC
        return (tf.keras.models.load_model('./ml/inverted_lookback_6_64x64_inverted_x2_kl0001_clip025'), lookback)

    lookback = 72
    simplemodel = SimpleStrategy()
    return (simplemodel, lookback)

def predict(model, state):
    state = tf.data.Dataset.from_tensors(state)
    state = state.with_options(options)

    action_probs = model.predict(state.batch(len(state)))

    action = np.argmax(action_probs[0])
    print("prediction results ", action_probs, "choosing action ", action)

    return action
