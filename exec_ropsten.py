import os
from strategy import fetch_and_rebalance

fetch_and_rebalance('ropsten', os.environ['ROPSTEN_INFURA_URL'], os.environ['ROPSTEN_KEEPER'], os.environ['ROPSTEN_PK'])
