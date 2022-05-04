import numpy as np
import tensorflow as tf

# Disable AutoShard.
options = tf.data.Options()
options.experimental_distribute.auto_shard_policy = tf.data.experimental.AutoShardPolicy.OFF #AutoShardPolicy.DATA
LOOKBACK = 6

def load_model():
    return tf.keras.models.load_model('./ml/dataset_update_agent_pooling_x2')

def predict(model, state):
    state = tf.data.Dataset.from_tensors(state)
    state = state.with_options(options)

    action_probs = model.predict(state.batch(LOOKBACK))

    action = np.argmax(action_probs[0])
    print("prediction results ", action_probs, "choosing action ", action)

    return action
