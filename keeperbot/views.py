from django.http import HttpResponse
from web3 import Web3
import environ
import binascii
import time

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