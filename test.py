import binascii
from web3 import Web3
import os

keeper = '0xffa9FDa3050007645945e38E72B5a3dB1414A59b'
pk = os.environ['PK']
WEB3_INFURA_PROJECT_ID = os.environ['WEB3_INFURA_PROJECT_ID']

def test_transaction():
    web3 = Web3(Web3.HTTPProvider('https://ropsten.infura.io/v3/' + WEB3_INFURA_PROJECT_ID))
    balance = web3.eth.get_balance(keeper)

    print(balance)
    receiverAccount = '0xaaB5a17c0d9d09632F013d8b5E2353A77710dDc1'

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

