import math

import numpy as np
import gym


class PriceEnv(gym.Env):
    RANGE_FACTOR = 2
    RANGES = [0, 0.000005, 0.00001, 0.000015, 0.00002, 0.00003, 0.00004, 0.00005, 0.00006]
    POOL_FEE = 0.05 / 100

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

    def swap(self, percentage_token0, price):
        assets = self.il[0] + self.il[1] * price
        self.il[0] = assets * percentage_token0
        self.il[1] = assets * (1 - percentage_token0) / price

    def step(self, action):

        reward = 0
        fees = 0

        old_price = self.prices[self.price_index]
        old_assets_price = self.il[0] + self.il[1] * old_price

        if action != 0:
            fees = 0.5

            if action == 1:  # increment
                self.current_action_range = min(self.current_action_range + 1, len(PriceEnv.RANGES) - 1)
            if action == 2:  # decrement
                self.current_action_range = max(self.current_action_range - 1, 0)

            self.__update_last_action_price()

            # IL rebalance
            assets = self.il[0] + self.il[1] * self.current_price()
            self.il[0] = assets / 2
            self.il[1] = assets / 2 / self.current_price()

            self.il[0] -= PriceEnv.POOL_FEE * self.il[0]
            self.il[1] -= PriceEnv.POOL_FEE * self.il[1]

        new_price = self.prices[self.price_index + 1]
        lower_bound = self.last_action_price[0]
        upper_bound = self.last_action_price[1]
        center = (lower_bound + upper_bound) / 2

        price_difference = 0
        given_range = upper_bound - lower_bound

        if self.current_action_range > 0 and given_range > 0:
            # In range price
            if lower_bound <= new_price <= upper_bound:
                reward += 0.000005 / given_range

                # IL
                # [10,0] p=6 -> 40% token1, 60% token0

                self.swap((new_price - lower_bound) / given_range, new_price)

            elif self.il[0] > 0 and self.il[1] > 0:
                # outside given range, used all liquidity
                if new_price < lower_bound:
                    # price decrease, more token
                    self.il[1] += self.il[0] / lower_bound
                    self.il[0] = 0
                else:
                    # price increase, more fiat
                    self.il[0] += self.il[1] * upper_bound
                    self.il[1] = 0

        self.price_index += 1

        done = self.price_index >= len(self.prices) - 1  # is there still data left?
        price_difference = new_price - center

        # calculate IL
        new_assets_price = self.il[0] + self.il[1] * new_price
        pool_il_difference = new_assets_price - old_assets_price

        new_investment_price = self.investment[0] + self.investment[1] * new_price
        old_investment_price = self.investment[0] + self.investment[1] * old_price
        hold_il_difference = (new_investment_price - old_investment_price)
        il_difference = (pool_il_difference - hold_il_difference) * 0.01

        info = {}
        return [price_difference, self.current_action_range_val(), il_difference, reward - fees], il_difference + reward - fees, done, info

    def reset(self):
        self.price_index = len(self.prices) - 10000
        self.intial_price = self.price_index
        self.current_action_range = 1
        self.__update_last_action_price()
        eth = 1
        self.il = [eth, eth/self.current_price()]
        self.investment = [eth, eth/self.current_price()]
        return [0, self.current_action_range_val(), 0, 0]

    def seed(self, seed):
        self.price_index = seed
        self.intial_price = self.price_index
        self.current_action_range = 1
        self.__update_last_action_price()
        eth = 1
        self.il = [eth, eth/self.current_price()]
        self.investment = [eth, eth/self.current_price()]
        return [0, self.current_action_range_val(), 0, 0]

    def __update_last_action_price(self):
        self.last_action_price = [max(0, self.prices[self.price_index] - self.current_action_range_val()),
                                  self.prices[self.price_index] + self.current_action_range_val()]

    def current_action_range_val(self):
        return PriceEnv.RANGES[self.current_action_range]

    def current_price(self):
        return self.prices[self.price_index]

    def reset_status_and_price(self, price, il, range_val, last_action_price, investment):
        self.prices = [1/price]
        self.price_index = 0
        self.intial_price = self.price_index
        self.current_action_range = PriceEnv.RANGES.index(range_val)
        self.last_action_price = last_action_price
        self.il = il
        # we are given investment=[USD, ETH]
        # invert it because we use inverted price, so we express things in ETH
        self.investment = [investment[1], investment[0]]
        return [0, self.current_action_range_val(), 0, 0]

    def add_price(self, price):
        self.prices.append(1/int(price))

    def current_action_range_converted(self):
        return 1/10 - 1/(self.current_action_range_val()+10) # TODO: don't how else to do this

    def prepare_bounds_for_env(self, data):
        lower_base = min(data["baseLower"], data["baseUpper"])
        upper_base = max(data["baseLower"], data["baseUpper"])

        lower_limit = min(data["limitLower"], data["limitUpper"])
        upper_limit = max(data["limitLower"], data["limitUpper"])

        #if data["token0_quantity"] <= 0.01 or data["token1_quantity"] <= 1e-10:
        #    # use limit because we are unbalanced
        #    lower_bound = data["limitLower"]
        #    upper_bound = data["limitUpper"]

        lower_bound = min(lower_base, lower_limit)
        upper_bound = max(upper_base, upper_limit)

        return [1/lower_bound, 1/upper_bound]
