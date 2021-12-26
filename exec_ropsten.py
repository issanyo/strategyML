import os
from .strategy_brownie import fetch_and_rebalance

fetch_and_rebalance('ropsten', os.environ['ROPSTEN_KEEPER'], os.environ['ROPSTEN_PK'])
