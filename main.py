import os
from .strategy_brownie import fetch_and_rebalance

def main():
    fetch_and_rebalance(os.environ['VAULT_CONFIG'], os.environ['ROPSTEN_KEEPER'], os.environ['ROPSTEN_PK'])
