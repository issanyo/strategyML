import os

keeper = os.environ['KEEPER']
pk = os.environ['PK']


def rebalance(limit_lower, base_lower, strategy, web3):
    print('Rebalancing')
    print(pk)
    print(strategy.functions.keeper().call())
    print(str(web3.eth.generate_gas_price()))

    try:

        print('setBaseThreshold')
        nonce = web3.eth.getTransactionCount(keeper)
        tx = strategy.functions.setBaseThreshold(base_lower).buildTransaction(
        {
            'value': 0,
            'chainId': 3,
            'gas': web3.eth.generate_gas_price(),
            'nonce': nonce
        })
        signed_tx = web3.eth.account.sign_transaction(tx, private_key = pk)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)

        print('setLimitThreshold')
        nonce = web3.eth.getTransactionCount(keeper)
        tx = strategy.functions.setLimitThreshold(limit_lower).buildTransaction(
        {
            'value': 0,
            'chainId': 3,
            'gas': web3.eth.generate_gas_price(),
            'nonce': nonce
        })
        signed_tx = web3.eth.account.sign_transaction(tx, private_key = pk)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)

        print('rebalance tx')
        nonce = web3.eth.getTransactionCount(keeper)
        tx = strategy.functions.rebalance().buildTransaction(
        {
            'value': 0,
            'chainId': 3,
            'gas': web3.eth.generate_gas_price(),
            'nonce': nonce
        })
        signed_tx = web3.eth.account.sign_transaction(tx, private_key = pk)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)

        print('Rebalance successful')
    except Exception as e:
        print(e)
        print('Rebalance failed')
    return
    
