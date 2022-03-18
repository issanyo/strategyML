import os
from .strategy import fetch_and_rebalance

def main():
    fetch_and_rebalance('arbitrum', os.environ['ROPSTEN_KEEPER'], os.environ['ROPSTEN_PK'])
