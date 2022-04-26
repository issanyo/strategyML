import numpy as np
import tensorflow as tf

# Disable AutoShard.
options = tf.data.Options()
options.experimental_distribute.auto_shard_policy = tf.data.experimental.AutoShardPolicy.OFF #AutoShardPolicy.DATA
LOOKBACK = 6

def load_model():
    return tf.keras.models.load_model('./ml/lookback_6_64x64_kl0001_clip025_new_ranges_max')

def predict(model, state):
    state = tf.data.Dataset.from_tensors(state)
    state = state.with_options(options)

    action_probs = model.predict(state.batch(LOOKBACK))

    action = np.argmax(action_probs[0])
    print("prediction results ", action_probs, "choosing action ", action)

    return action
