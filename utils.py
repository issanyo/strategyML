
   
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
    con = psycopg2.connect(
        host = os.environ['host'],
        database = os.environ['database'],
        user = os.environ['user'],
        password = os.environ['password']
    )

    return con
