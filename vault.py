import math

def get_vault_data(vault, strategy, web3, abi):
    data = {}
    data['total0'], data['total1'] = vault.functions.getTotalAmounts().call()
    token0 = web3.eth.contract(vault.functions.token0().call(), abi=abi['MockToken'])
    token1 = web3.eth.contract(vault.functions.token1().call(), abi=abi['MockToken'])

    decimals_token_0 = token0.functions.decimals().call()
    decimals_token_1 = token1.functions.decimals().call()

    data['baseLower'] = math.pow(1.0001, -1 * abs(vault.functions.baseLower().call())) * math.pow(10, abs(decimals_token_0 - decimals_token_1))
    data['baseUpper'] = math.pow(1.0001, -1 * abs(vault.functions.baseUpper().call())) * math.pow(10, abs(decimals_token_0 - decimals_token_1))
    data['limitUpper'] = math.pow(1.0001, -1 * abs(vault.functions.limitUpper().call())) * math.pow(10, abs(decimals_token_0 - decimals_token_1))
    data['limitLower'] = math.pow(1.0001,  -1 * abs(vault.functions.limitLower().call())) * math.pow(10, abs(decimals_token_0 - decimals_token_1))
        
    data['outstandingShares'] = vault.functions.totalSupply().call()
    data['tick'] = strategy.functions.getTick().call()

    data['price'] = 1.001 ** data['tick'] * 10 ** (decimals_token_0 - decimals_token_1)

    data['tvl'] = data['price'] * data['total1']
    print('total0: ' + str(data['total0']) + '\n' + 'total1: ' + str(data['total1']) + '\n' + 'baseLower is ' + str(data['baseLower']) + '\n' + 'baseUpper is ' + str(data['baseUpper']) + '\n' + 'limitUpper is ' + str(data['limitUpper']) + '\n' + 'limitLower is ' + str(data['limitLower']) + '\n' + 'outstanding shares is ' + str(data['outstandingShares']) + '\n' + 'tick is ' + str(data['tick']) + '\n' + 'price is ' + str(data['price']) + '\n' + 'tvl is ' + str(data['tvl']) + '\n')
    return data