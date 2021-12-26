import os
from .strategy_brownie import fetch_and_rebalance

def main():
    fetch_and_rebalance('arbitrum', os.environ['ROPSTEN_KEEPER'], os.environ['ROPSTEN_PK'])
