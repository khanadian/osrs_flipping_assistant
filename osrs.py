import requests
from requests.auth import HTTPDigestAuth
import json
import time
import pandas as pd
import math
import gspread


url = "https://prices.runescape.wiki/api/v1/osrs/latest"
url2 = "https://oldschool.runescape.wiki/?title=Module:GEIDs/data.json&action=raw&ctype=application%2Fjson"
url3 = "https://prices.runescape.wiki/api/v1/osrs/mapping"
url4 = "https://prices.runescape.wiki/api/v1/osrs/5m"
url5 = "https://prices.runescape.wiki/api/v1/osrs/1h"
url6 = "https://prices.runescape.wiki/api/v1/osrs/24h"

headers = {
    'User-Agent': 'flip finder',
    'From': 'khanadian'
    }

response = requests.get(url, headers=headers)
r2 = requests.get(url2, headers=headers)

df = pd.DataFrame(columns=['item', 'low', 'high', 'profit', "ROI", "limit", \
                           "potential", "cost", "5m volume", "1h volume",\
                           "24h volume", "avg Low diff", "avg high diff", 'miss'])
df_avg = pd.DataFrame(columns=['item', 'timestamp', 'low', 'high', 'lovolume',\
                               'hivolume'])
                               
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
                roi = round(profit / high, 3)
                
                df.loc[int(k)] = [inv_items[int(k)], low, high, profit, roi, 1, \
                                  0, 0, 0, 0, 0, "N/A", "N/A", 0]

                
r3 = requests.get(url3, headers=headers)

if r3.ok:
    mapping = json.loads(r3.content)
    mpp = {}
    for item in mapping:
        try:
            lim = item["limit"]
        except:
            lim = 1

        try:
            df.at[item["id"], "potential"] = lim * df.at[item["id"], "profit"]
            df.at[item["id"], "cost"] = lim * df.at[item["id"], "low"]
            df.at[item["id"], "limit"] = lim
        except:
            print(item["name"])


r4 = requests.get(url4, headers=headers)
if r4.ok:
    output = json.loads(r4.content)
    for data in output:
        if type(output[data]) == int:
            continue
        for key in output[data]:
            try:
                hivolume = output[data][key]['highPriceVolume']
                lovolume = output[data][key]['lowPriceVolume']                  
                ratio = round((hivolume * lovolume)/(df.at[int(key), "limit"]**2), 4)
                df.at[int(key), "5m volume"] = round(math.log(hivolume+1) * math.log(lovolume+1), 2)
            except:
                print(key)

for i in range(1, 19):
    timestamp = str(round((int(time.time())-(300*i))/300)*300) #must be nearest 300)
    url4a = url4 + "?timestamp="+timestamp
    r4 = requests.get(url4a, headers=headers)
    if r4.ok:
        output = json.loads(r4.content)
        for data in output:
            if type(output[data]) == int:
                continue
            for key in output[data]:
                try:
                    hivolume = output[data][key]['highPriceVolume']
                    lovolume = output[data][key]['lowPriceVolume']
                    if hivolume == 0 or lovolume == 0:
                        df.at[int(key), "miss"] += 1
                    hiprice = output[data][key]['avgHighPrice']
                    loprice = output[data][key]['avgLowPrice']

                    df_avg.loc[key + "-"+timestamp] = [df.at[int(key), \
                                        'item'], timestamp, loprice, hiprice, \
                                                        lovolume, hivolume]
                except:
                    print(key)
    else:
        print(url4a)
    time.sleep(1)

print(df_avg)

                
r5 = requests.get(url5, headers=headers)

if r5.ok:
    output = json.loads(r5.content)
    for data in output:
        if type(output[data]) == int:
            continue
        for key in output[data]:
            avgLow = output[data][key]['avgLowPrice']
            avgHigh = output[data][key]['avgHighPrice']
            hvolume = output[data][key]['highPriceVolume']
            lvolume = output[data][key]['lowPriceVolume']
            if avgLow and avgHigh:
                df.at[int(key), "avg Low diff"] = df.at[int(key), "low"] - avgLow
                df.at[int(key), "avg high diff"] = df.at[int(key), "high"] - avgHigh
                df.at[int(key), "1h volume"] = round(math.log(hvolume+1) * math.log(lvolume+1), 2)

r6 = requests.get(url6, headers=headers)

if r6.ok:
    output = json.loads(r6.content)
    for data in output:
        if type(output[data]) == int:
            continue
        for key in output[data]:
            avgLow = output[data][key]['avgLowPrice']
            avgHigh = output[data][key]['avgHighPrice']
            hvolume = output[data][key]['highPriceVolume']
            lvolume = output[data][key]['lowPriceVolume']
            if avgLow and avgHigh:
                df.at[int(key), "avg Low diff"] = df.at[int(key), "low"] - avgLow
                df.at[int(key), "avg high diff"] = df.at[int(key), "high"] - avgHigh
                df.at[int(key), "24h volume"] = round(math.log(hvolume+1) * math.log(lvolume+1), 2)



print(df)
df.to_csv('out.csv', index=False)

gc = gspread.service_account()
sh = gc.open("OSRS flipper")
content = open('out.csv', 'r').read()
gc.import_csv("1hVK-tNyGvI6lo993CjfWbiQz6mlt2OaMWEMXOdUIJWg", content)

