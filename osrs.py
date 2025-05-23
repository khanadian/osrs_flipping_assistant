import requests
from requests.auth import HTTPDigestAuth
import json
import time
import pandas as pd
import math
import gspread
import statistics

URL = "https://prices.runescape.wiki/api/v1/osrs/latest"
URL_ID = "https://oldschool.runescape.wiki/?title=Module:GEIDs/data.json&action=raw&ctype=application%2Fjson"
URL_INFO = "https://prices.runescape.wiki/api/v1/osrs/mapping"
URL_5m = "https://prices.runescape.wiki/api/v1/osrs/5m"
URL_1h = "https://prices.runescape.wiki/api/v1/osrs/1h"
URL_24h = "https://prices.runescape.wiki/api/v1/osrs/24h"


headers = {
    'User-Agent': 'flip finder',
    'From': 'khanadian'
    }

#getting the info on all of the items and populating the dataframe
response = requests.get(URL, headers=headers)
r2 = requests.get(URL_ID, headers=headers)

df = pd.DataFrame(columns=['item', 'low', 'high', 'profit', "ROI", "limit", \
                           "potential", "cost", "5m volume", "1h volume",\
                           "24h volume", "volume avg", "miss", "volume diff", "score"])
df_avg = pd.DataFrame(columns=['item', 'timestamp', 'low', 'high', 'lovolume',\
                               'hivolume'])
                               
if r2.ok:
    items = json.loads(r2.content)
    inv_items = {v: k for k,v in items.items()}
else:
    print("r2 fail")
if response.ok:
    data = json.loads(response.content)

    for key in data:
        
        for k in data[key]:
            if int(k) in inv_items.keys():
                high = int(data[key][k]["high"])
                low = int(data[key][k]["low"])
                
                df.loc[int(k)] = [inv_items[int(k)], low, high, 0, 0, 1, \
                                  0, 0, 0, 0, 0, 0, 0, 0, 0]
else:
    print("r fail")

#grabbing the 5-minute info
r4 = requests.get(URL_5m, headers=headers)
if r4.ok:
    output = json.loads(r4.content)
    for data in output:
        if type(output[data]) == int:
            continue
        for key in output[data]:
            try:
                hivolume = output[data][key]['highPriceVolume']
                lovolume = output[data][key]['lowPriceVolume']                  
                df.at[int(key), "5m volume"] = hivolume+lovolume
            except:
                continue
                #print(key)
else:
    print("r4 fail")

#calculating the averaged low, high, and misses
attempts = 18
for i in range(1, attempts):
    timestamp = str(round((int(time.time())-(300*i))/300)*300) #must be nearest 300)
    URL_5ma = URL_5m + "?timestamp="+timestamp
    r4 = requests.get(URL_5ma, headers=headers)
    if r4.ok:
        output = json.loads(r4.content)
        for data in output:
            if type(output[data]) == int:
                continue
            for key in output[data]:
                try:
                    hivolume = output[data][key]['highPriceVolume']
                    lovolume = output[data][key]['lowPriceVolume']
                    if hivolume == 0:
                        df.at[int(key), "miss"] += 1
                    if lovolume == 0:
                        df.at[int(key), "miss"] += 1
                    hiprice = output[data][key]['avgHighPrice']
                    loprice = output[data][key]['avgLowPrice']

                    df_avg.loc[key + "-"+timestamp] = [df.at[int(key),'item'], \
                            timestamp, loprice, hiprice, lovolume, hivolume]
                except:
                    print(key)
    else:
        print(URL_5ma)
    time.sleep(1)

#print(df_avg)
#df_avg.to_csv('out2.csv', index=False)

#calculating the profit, return on investment, and total misses with taxes factored in
for ind in df.index:
    temp_df = df_avg[df_avg.index.str.startswith(str(ind)+"-")]
    low = list(filter(lambda item: item is not None, temp_df["low"]))
    high = list(filter(lambda item: item is not None, temp_df["high"]))
    try:
        low = statistics.median(low)
        high = statistics.median(high)
    except Exception as e:
        low = 2
        high = 1
    
    try:
        tax = int(math.floor(high * 0.01))
    except:
        tax = int(math.floor(df.at[ind, "high"] * 0.01))
    profit = high - low - tax
    df.at[ind, "profit"] = profit
    df.at[ind, "ROI"] = round(profit / high * 100, 3)
    df.at[ind, "miss"] += (attempts-len(temp_df.index))

#calculating the potential and cost based on the limit             
r3 = requests.get(URL_INFO, headers=headers)

if r3.ok:
    mapping = json.loads(r3.content)
    mpp = {}
    for item in mapping:
        try:
            lim = item["limit"]
        except:
            lim = 1

        try:
            df.at[item["id"], "potential"] = round(lim * df.at[item["id"], "profit"]/1000, 2)
            df.at[item["id"], "cost"] = round(lim * df.at[item["id"], "low"]/1000000, 2)
            df.at[item["id"], "limit"] = lim
        except:
            print(item["name"])
else:
    print("r3 fail")

#adding data for 1-hour
r5 = requests.get(URL_1h, headers=headers)

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
                try:
                    df.at[int(key), "1h volume"] = round((hvolume+lvolume)/df.at[int(key), "limit"], 3)
                except:
                    continue #only an issue for newly released content and items
else:
    print("r5 fail")

#adding data for 24 hours, normalizing the 5 minute and 24 hour data with the 1-hour data for easier comparability
r6 = requests.get(URL_24h, headers=headers)

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
                df.at[int(key), "5m volume"] = round(df.at[int(key), "5m volume"]/df.at[int(key), "limit"]\
                                               *12, 3)
                df.at[int(key), "24h volume"] = round((hvolume+lvolume)/df.at[int(key), "limit"]/24, 3)
                df.at[int(key), "volume avg"] = round(statistics.median([df.at[int(key), "5m volume"],
                            df.at[int(key), "1h volume"],  df.at[int(key), "24h volume"]]), 3)

                volumediff = hvolume/lvolume
                if volumediff < 1:
                    volumediff = 1/volumediff

                df.at[int(key), "volume diff"] = round(volumediff, 3)
                
else:
    print("r6 fail")

#calculating score
numerator = df["potential"] * df["volume avg"] * abs((abs(df["ROI"]+1)**0.5) - 1.4)
denominator = ((1+df["miss"])*(1+df["volume diff"]))**2
df["score"] = round(numerator/denominator, 3)

#outputting
print(df)
df.to_csv('out.csv', index=False)

gc = gspread.service_account()
sh = gc.open("OSRS flipper")
content = open('out.csv', 'r').read()
gc.import_csv("1hVK-tNyGvI6lo993CjfWbiQz6mlt2OaMWEMXOdUIJWg", content)

