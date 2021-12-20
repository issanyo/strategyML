
   
import json
import os
import psycopg2

def get_contract_abi():
    fObj = open('./AlphaVault.json',)
    AlphaVault = json.load(fObj)['abi']
    fObj = open('./DynamicRangesStrategy.json')
    DynamicRangesStrategy = json.load(fObj)['abi']
    fObj = open('./MockToken.json')
    MockToken = json.load(fObj)['abi']

    abi = {
        'AlphaVault': AlphaVault,
        'DynamicRangesStrategy': DynamicRangesStrategy,
        'MockToken': MockToken
    }

    return abi

def connect_db():
    print('Connecting to DB...')
    print(os.environ['HOST'])
    print(os.environ['DATABASE'])
    print(os.environ['USER'])
    print(os.environ['PASSWORD'])
    con = psycopg2.connect(
        host = os.environ['HOST'],
        database = os.environ['DATABASE'],
        user = os.environ['USER'],
        password = os.environ['PASSWORD']
    )

    return con
