import math

import numpy as np
import gym


class PriceEnv(gym.Env):
    RANGE_FACTOR = 2
    RANGES = [10, 20, 30, 40, 60, 80, 100, 150, 200, 300, 400, 500, 700, 900]

    def __init__(self, prices):
        """
        actions:
        0 -> keep
        1 -> increment
        2 -> decrement
        3 -> recenter with current settings
        """
        self.price_index = None
        self.action_space = gym.spaces.Discrete(4)
        self.observation_space = gym.spaces.Box(low=np.array([-1000., 10, 0, 0]), high=np.array([1000., 900, 10000, 1]))
        self.prices = prices
        # need to call reset or seed

    def step(self, action):

        reward = 0
        fees = 0

        old_price = self.prices[self.price_index]
        old_assets_price = self.il[0] + self.il[1] * old_price

        if action != 0:
            fees = 0.1  # fees for changing range

            if action == 1:  # increment
                self.current_action_range = min(self.current_action_range + 1, len(PriceEnv.RANGES) - 1)
            if action == 2:  # decrement
                self.current_action_range = max(self.current_action_range - 1, 0)

            self.__update_last_action_price()

            # IL rebalance
            assets = self.il[0] + self.il[1] * self.current_price()
            self.il[0] = assets / 2
            self.il[1] = assets / 2 / self.current_price()

        new_price = self.prices[self.price_index + 1]
        lower_bound = self.last_action_price[0]
        upper_bound = self.last_action_price[1]
        center = (lower_bound + upper_bound) / 2

        price_difference = 0
        # In range price
        if lower_bound <= new_price <= upper_bound and self.il[0] > 0 and self.il[1] > 0:
            given_range = upper_bound - lower_bound

            reward += 1 / given_range if given_range > 0 else 0.5

            # IL

            # this is an aproximation, need to be checked again
            quantity_used_token0 = reward * new_price
            quantity_used_token1 = reward

            if old_price > new_price:
                # price decrease, more token
                self.il[0] -= quantity_used_token0
                self.il[1] += quantity_used_token1
            else:
                # price increase, more fiat
                self.il[0] += quantity_used_token0
                self.il[1] -= quantity_used_token1

        self.price_index += 1

        done = self.price_index >= len(self.prices) - 1  # is there still data left?
        price_difference = new_price - center

        # calculate IL
        new_assets_price = self.il[0] + self.il[1] * new_price
        il_difference = (new_assets_price - old_assets_price) * 0.01

        info = {}
        #return np.around([price_difference, self.current_action_range_val(), il_difference, reward - fees], decimals=4), il_difference + reward - fees, done, info
        return [price_difference, self.current_action_range_val(), il_difference, reward - fees], il_difference + reward - fees, done, info

    def reset(self):
        self.price_index = len(self.prices) - 10000
        self.intial_price = self.price_index
        self.current_action_range = 0
        self.__update_last_action_price()
        self.il = [self.current_price(), 1]
        self.assets_price = self.il[0] + self.il[1] * self.current_price()
        return [0, self.current_action_range_val(), 0, 0]

    def seed(self, seed):
        self.price_index = seed
        self.intial_price = self.price_index
        self.current_action_range = 0
        self.__update_last_action_price()
        self.il = [self.current_price(), 1]
        self.assets_price = self.il[0] + self.il[1] * self.current_price()
        return [0, self.current_action_range_val(), 0, 0]

    def __update_last_action_price(self):
        self.last_action_price = [max(0, self.prices[self.price_index] - 1 - self.current_action_range_val()),
                                  self.prices[self.price_index] + 1 + self.current_action_range_val()]

    def current_action_range_val(self):
        return PriceEnv.RANGES[self.current_action_range]

    def current_price(self):
        return self.prices[self.price_index]

    def reset_status_and_price(self, price, il, range_val, last_action_price):
        self.prices = [price]
        self.price_index = 0
        self.intial_price = self.price_index
        self.current_action_range = PriceEnv.RANGES.index(range_val)
        self.last_action_price = last_action_price
        self.il = il
        self.assets_price = self.il[0] + self.il[1] * self.current_price()
        return [0, self.current_action_range_val(), 0, 0]

    def add_price(self, price):
        self.prices.append(price)


def prepare_bounds_for_env(data):
    lower_bound = data["baseLower"]
    upper_bound = data["baseUpper"]

    if data["token0_quantity"] <= 0.01 or data["token1_quantity"] <= 1e-10:
        # use limit because we are unbalanced
        lower_bound = data["limitLower"]
        upper_bound = data["limitUpper"]

    if lower_bound > upper_bound:
        tmp = lower_bound
        lower_bound = upper_bound
        upper_bound = tmp
    return [math.floor(lower_bound), math.ceil(upper_bound)]
