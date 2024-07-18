import requests
from requests.auth import HTTPDigestAuth
import json

import pandas as pd
import math

url = "https://prices.runescape.wiki/api/v1/osrs/latest"
url2 = "https://oldschool.runescape.wiki/?title=Module:GEIDs/data.json&action=raw&ctype=application%2Fjson"
url3 = "https://prices.runescape.wiki/api/v1/osrs/mapping"
url4 = "https://prices.runescape.wiki/api/v1/osrs/1h"

headers = {
    'User-Agent': 'flip finder',
    'From': 'khanadian'
    }

response = requests.get(url, headers=headers)
r2 = requests.get(url2, headers=headers)

df = pd.DataFrame(columns=['item', 'low', 'high', 'profit', "limit", \
                           "potential", "cost", "1h volume", "avg Low diff"])

if r2.ok:
    items = json.loads(r2.content)
    inv_items = {v: k for k,v in items.items()}
    
if response.ok:
    data = json.loads(response.content)

    for key in data:
        
        for k in data[key]:
            if int(k) in inv_items.keys():
                high = int(data[key][k]["high"])
                tax = int(math.floor(high * 0.01))
                low = int(data[key][k]["low"])
                profit = high - low - tax - 2 #subtract 2 to play margins
                
                df.loc[int(k)] = [inv_items[int(k)], low, high, profit, 0, 0, 0, 0, "N/A"]

                
r3 = requests.get(url3, headers=headers)

if r3.ok:
    mapping = json.loads(r3.content)
    mpp = {}
    for item in mapping:
        try:
            df.at[item["id"], "potential"] = item["limit"] * df.at[item["id"], "profit"]
            df.at[item["id"], "cost"] = item["limit"] * df.at[item["id"], "low"]
            df.at[item["id"], "limit"] = item["limit"]
        except:
            print(item["name"])

r4 = requests.get(url4, headers=headers)

if r4.ok:
    output = json.loads(r4.content)
    for data in output:
        if type(output[data]) == int:
            continue
        for key in output[data]:
            hivolume = output[data][key]['highPriceVolume']
            lovolume = output[data][key]['lowPriceVolume']
            df.at[int(key), "1h volume"] = hivolume + lovolume
            avgLow = output[data][key]['avgLowPrice']
            if avgLow:
                df.at[int(key), "avg Low diff"] = df.at[int(key), "low"] - avgLow


print(df)
df.to_csv('out.csv', index=False)
