from web3 import Web3

import binascii
import requests
from datetime import datetime
import json
import numpy as np
from utils import getContractAbi, connectDB
import os
import psycopg2




def test_transaction():
    pk = '6000e057971f9f094145f7f5a088b6a277eb904ec77288ec873aedca9fafcb7f'
    WEB3_INFURA_KEY = 'cf01a35558ad4215aebc2042577b2f23'
    web3 = Web3(Web3.HTTPProvider('https://ropsten.infura.io/v3/' + WEB3_INFURA_KEY))
    balance = web3.eth.get_balance('0xffa9FDa3050007645945e38E72B5a3dB1414A59b')

    print(balance)
    receiverAccount = '0xaaB5a17c0d9d09632F013d8b5E2353A77710dDc1'
    keeper = '0xffa9FDa3050007645945e38E72B5a3dB1414A59b'

    nonce = web3.eth.getTransactionCount(keeper)

    transaction  = {
        'to': receiverAccount,
        'value': 370000000000000,
        'gas': 2000000,
        'chainId': 3,
        'gasPrice': 200000000000,
        'nonce': nonce
    }
    
    
    signed_transaction = web3.eth.account.sign_transaction(transaction, pk)
    
    print('signed transaction hash is ' + str(binascii.hexlify(signed_transaction.hash)))
    hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    web3.eth.wait_for_transaction_receipt(hash)


    print('transaction returns hash as: ' + str(hash))

    newBalance = web3.eth.get_balance(keeper)
    print(newBalance)


def fetch():
    WEB3_INFURA_KEY = 'cf01a35558ad4215aebc2042577b2f23'
    abi = getContractAbi()
    con = connectDB()

    web3 = Web3(Web3.HTTPProvider('https://ropsten.infura.io/v3/' + WEB3_INFURA_KEY))
    vault = web3.eth.contract('0x624633fD2Eff00cBFC7294CABD80303b12C5fD9d', abi=abi['AlphaVault'])
    strategy = web3.eth.contract('0x4Bb99cfEe541C66a79D4DaeB4431BCfe8de1d410', abi=abi['DynamicRangesStrategy'])

    total0, total1 = vault.functions.getTotalAmounts().call()

    baseLower = vault.functions.baseLower().call()
    baseUpper = vault.functions.baseUpper().call()

    limitUpper = vault.functions.limitUpper().call()
    limitLower = vault.functions.limitLower().call()
        
    outstandingShares = vault.functions.totalSupply().call()
    
    tick = strategy.functions.getTick().call()
    

    token0 = web3.eth.contract(vault.functions.token0().call(), abi=abi['MockToken'])
    token1 = web3.eth.contract(vault.functions.token1().call(), abi=abi['MockToken'])

    decimals_token_0 = token0.functions.decimals().call()
    decimals_token_1 = token1.functions.decimals().call()

    price = 1.001 ** tick * 10 ** (decimals_token_0 - decimals_token_1)

    tvl = price * total1
    timestamp = datetime.now()

    print('total0: ' + str(total0) + '\n' + 'total1: ' + str(total1) + '\n' + 'baseLower is ' + str(baseLower) + '\n' + 'baseUpper is ' + str(baseUpper) + '\n' + 'limitUpper is ' + str(limitUpper) + '\n' + 'limitLower is ' + str(limitLower) + '\n' + 'outstanding shares is ' + str(outstandingShares) + '\n' + 'tick is ' + str(tick) + '\n' + 'price is ' + str(price) + '\n' + 'tvl is ' + str(tvl) + '\n')

    cur = con.cursor()
    
    cur.execute("INSERT INTO keeperbot_data (token0_quantity, token1_quantity, \"baseLower\", \"baseUpper\", \"limitUpper\", \"limitLower\", \"totalSupply\", \"priceStrategy\", tvl, pool_address, strategy_address, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (total0, total1, baseLower, baseUpper, limitUpper, limitLower, outstandingShares, price, tvl, '0x624633fD2Eff00cBFC7294CABD80303b12C5fD9d', '0x4Bb99cfEe541C66a79D4DaeB4431BCfe8de1d410', timestamp))

    con.commit()

    con.close()


fetch()