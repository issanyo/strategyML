from django.http import HttpResponse
from web3 import Web3
import environ
import binascii
import requests
import pandas as pd
from datetime import datetime
import json
import numpy as np


env = environ.Env()
environ.Env.read_env()

def index(request):
    pk = env('PK')
    WEB3_INFURA_KEY = env('WEB3_INFURA_KEY')
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

    return HttpResponse('Transaction sent by ' + keeper + ' to ' + receiverAccount + ' with value ' + str(transaction['value']) + '.\n Previous balance was ' + str(balance) + ', current balance is ' + str(newBalance) + '.\n')


def fetch(request):
    WEB3_INFURA_KEY = env('WEB3_INFURA_KEY')
    fObj = open('./keeperbot/AlphaVaultABI.json',)
    AlphaVaultABI = json.load(fObj)['abi']

    web3 = Web3(Web3.HTTPProvider('https://ropsten.infura.io/v3/' + WEB3_INFURA_KEY))
    vault = web3.eth.contract('0x130c973Bbe11CBc5BAE094a45710CDE4Bebb8438', abi=AlphaVaultABI)
    print(vault.address)

    total0, total1 = vault.functions.getTotalAmounts().call()

    print(total0)
    print(total1)

    baseLower = vault.functions.baseLower().call()
    baseUpper = vault.functions.baseUpper().call()

    print(baseLower)
    print(baseUpper)
    
    limitLower = vault.functions.limitLower().call()
    limitUpper = vault.functions.limitUpper().call()

    print(limitLower)
    print(limitUpper)


    return HttpResponse('Vault address is ' + vault.address)