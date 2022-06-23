import numpy as np

class SimpleStrategy:
    """
    actions:
    0 -> keep
    1 -> increment
    2 -> decrement
    3 -> recenter with current settings
    """
    RANGES = [0, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.4, 0.6, 0.8]

    def predict(self, state):
        action = 0

        data = list(state.as_numpy_iterator())[0][0]
        # data = state
        q = len(data) // 2

        deviation = data[:, 0].std()
        mean = np.sqrt((data[:, 0] ** 2).mean())

        reward = data[:, 3].sum()
        max_reward = np.array([0.025 / d for d in data[:, 1]]).sum()  # 0.025/ given_range
        p_reward = reward / max_reward
        p_reward_last_quartile = data[-q:, 3].sum() / np.array([0.025 / d for d in data[-q:, 1]]).sum()

        currently_inside_range = data[-1, 3] > 0

        # calculate weighted fees (recent are heavier)
        # 1+2+3+4+5
        # 1/15 + 2/15 + 3/15 + 4/15 + 5/15
        weight = q * (q + 1) / 2
        weights = np.arange(1, q + 1) / weight
        fees_last_quartile = np.average(data[-q:, 4], weights=weights)

        deviation_last_quartile = data[-q:, 0].std()  # np.abs(data[-1][0] - data[0][0])

        # curr_range = data[-1][1]
        # curr_range_index = SimpleStrategy.RANGES.index(curr_range)
        # larger_range = min(curr_range_index+1, len(SimpleStrategy.RANGES)-1)
        # smaller_range = max(curr_range_index-1, 0)

        p_outside_curr_range = np.sum(data[:, 3] == 0) / len(data[:, 3])
        p_above_curr_range = np.sum((data[:, 3] == 0) & (data[:, 0] > 0)) / len(data[:, 3])
        p_below_curr_range = np.sum((data[:, 3] == 0) & (data[:, 0] < 0)) / len(data[:, 3])

        trend_last_quartile = np.abs(
            np.average([data[i, 0] / (data[i, 1] / 2) for i in range(len(data) - q, len(data))],
                       weights=np.arange(1, q + 1) / (q * (q + 1) / 2)))

        # mean_reward >= -0.001 # are we paying too much for rebalance?

        print("currently_inside_range", currently_inside_range)
        print("trend_last_quartile", trend_last_quartile)
        print("p_reward_last_quartile", p_reward_last_quartile)
        print("deviation_last_quartile", deviation_last_quartile)
        print("fees_last_quartile", fees_last_quartile)
        print("p_reward", p_reward)
        print("deviation", deviation)
        print("p_outside_curr_range", p_outside_curr_range)
        print("p_above_curr_range", p_above_curr_range)
        print("p_below_curr_range", p_below_curr_range)

        # we are outside range and the price is not too volatile
        if fees_last_quartile < 0.1:

            if not currently_inside_range and 0.1 < p_reward < 0.75 and (
                    p_above_curr_range * p_below_curr_range > 0.001 or (
                    p_reward_last_quartile > 0.9 and p_outside_curr_range > 0.5)):
                # increment, outsiders up and down
                print("SimpleStrategy if#1")
                action = 1
            elif p_reward > 0.99 and p_reward_last_quartile > 0.99 and deviation < 0.1:
                # decrement, majourity of values are inside
                print("SimpleStrategy if#2")
                action = 2

            # check if we are still inside the current range
            elif deviation_last_quartile <= 0.25 and not currently_inside_range and p_reward_last_quartile < 0.5:  # mean > curr_range and
                print("SimpleStrategy if#3")
                action = 3

            # antecipate rebalance to prevent IL
            elif trend_last_quartile > 0.9:  # and deviation_last_quartile > 1:
                print("SimpleStrategy if#4")
                action = 3

        a = np.zeros(4)
        a[action] = 1
        return [a]
