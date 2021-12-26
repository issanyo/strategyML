import math
from brownie import Contract

def get_vault_data(vault, strategy, abi):
    data = {}
    data['total0'], data['total1'] = vault.getTotalAmounts()
    token0 = Contract("token0", address=vault.token0(), abi=abi['MockToken'])
    token1 = Contract("token1", address=vault.token1(), abi=abi['MockToken'])

    decimals_token_0 = token0.decimals()
    decimals_token_1 = token1.decimals()

    data['baseLower'] = math.pow(1.0001, -1 * abs(vault.baseLower())) * math.pow(10, abs(decimals_token_0 - decimals_token_1))
    data['baseUpper'] = math.pow(1.0001, -1 * abs(vault.baseUpper())) * math.pow(10, abs(decimals_token_0 - decimals_token_1))
    data['limitUpper'] = math.pow(1.0001, -1 * abs(vault.limitUpper())) * math.pow(10, abs(decimals_token_0 - decimals_token_1))
    data['limitLower'] = math.pow(1.0001,  -1 * abs(vault.limitLower())) * math.pow(10, abs(decimals_token_0 - decimals_token_1))
        
    data['outstandingShares'] = vault.totalSupply()
    data['tick'] = strategy.getTick()

    data['price'] = 1.001 ** data['tick'] * 10 ** (decimals_token_0 - decimals_token_1)

    data['tvl'] = data['price'] * data['total1']
    print('total0: ' + str(data['total0']) + '\n' + 'total1: ' + str(data['total1']) + '\n' + 'baseLower is ' + str(data['baseLower']) + '\n' + 'baseUpper is ' + str(data['baseUpper']) + '\n' + 'limitUpper is ' + str(data['limitUpper']) + '\n' + 'limitLower is ' + str(data['limitLower']) + '\n' + 'outstanding shares is ' + str(data['outstandingShares']) + '\n' + 'tick is ' + str(data['tick']) + '\n' + 'price is ' + str(data['price']) + '\n' + 'tvl is ' + str(data['tvl']) + '\n')
    return data
