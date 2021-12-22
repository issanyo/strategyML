import psycopg2

def insert_data(cur, con, vault_data, theGraphData, timestamp, last_rebalance, rebalance_check):
    try:
        cur.execute("INSERT INTO keeperbot_data (token0_quantity, token1_quantity, \"baseLower\", \"baseUpper\", \"limitUpper\", \"limitLower\", \"totalSupply\", \"priceStrategy\", tvl, pool_address, strategy_address, timestamp, price_graph, volume, liquidity, fees_pool, rebalance_check, rebalance_timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (vault_data['total0'], vault_data['total1'], vault_data['baseLower'], vault_data['baseUpper'], vault_data['limitUpper'], vault_data['limitLower'], vault_data['outstandingShares'], vault_data['price'], vault_data['tvl'], '0x624633fD2Eff00cBFC7294CABD80303b12C5fD9d', '0x4Bb99cfEe541C66a79D4DaeB4431BCfe8de1d410', timestamp, theGraphData['priceGraph'], theGraphData['volume'], theGraphData['liquidity'], theGraphData['fees_pool'], rebalance_check, last_rebalance))
        con.commit()
        print('Data successfully inserted')
    except psycopg2.Error as e:
        print(e)
        con.rollback()
