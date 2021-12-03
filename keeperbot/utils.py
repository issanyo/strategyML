import json

def getContractAbi():
    fObj = open('./keeperbot/AlphaVaultABI.json',)
    AlphaVault = json.load(fObj)['abi']
    fObj = open('./keeperbot/DynamicRangesStrategy.json')
    DynamicRangesStrategy = json.load(fObj)['abi']
    fObj = open('./keeperbot/MockToken.json')
    MockToken = json.load(fObj)['abi']

    abi = {
        'AlphaVault': AlphaVault,
        'DynamicRangesStrategy': DynamicRangesStrategy,
        'MockToken': MockToken
    }

    return abi