
   
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
        host='ec2-176-34-105-15.eu-west-1.compute.amazonaws.com',
        database='d25a74696pv5g',
        user='dhzryfbbhtkggy',
        password='421f0dfd4f65c2795d568c277fd55de894fe1667c3bed9d849715f1548e5bba1'
    )

    return con
