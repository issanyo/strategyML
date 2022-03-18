import json


def get_contract_abi():
    fObj = open('./abi/AlphaVault.json')
    AlphaVault = json.load(fObj)['abi']
    fObj = open('./abi/YoStrategy.json')
    YoStrategy = json.load(fObj)['abi']
    fObj = open('./abi/MockToken.json')
    MockToken = json.load(fObj)['abi']

    abi = {
        'AlphaVault': AlphaVault,
        'YoStrategy': YoStrategy,
        'MockToken': MockToken
    }
    return abi
