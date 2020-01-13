
#################################################################
# Поиск арбитражных пар. Пересчёт на рубли.
#################################################################

import requests
import json
from decimal import Decimal


# Получаем цены = list[str, str]
def GetInfo(pair):
    otvet = requests.get('https://yobit.net/api/3/depth/' + pair)
    data = json.loads(otvet.text)
    return data

    #Получаем i-ую от края цену
def Ask_Price(data, i):
    data["asks"] = data.get("asks", ["0", "0"])
    return Decimal(data["asks"][i][0]).quantize(Decimal("1.00000000"))
def Bid_Price(data, i):
    data["bids"] = data.get("bids", ["0", "0"])
    return Decimal(data["bids"][i][0]).quantize(Decimal("1.00000000"))

def inrurask(value, transpair):
    return (value * ASK_DICT[transpair]).quantize(Decimal("1.00000000"))
def inrurbid(value, transpair):
    return (value * BID_DICT[transpair]).quantize(Decimal("1.00000000"))

    ###############################################################################################################


# Получаем словарь с рублёвыми ценами основных тикетов
fivepairs = GetInfo('btc_rur-eth_rur-doge_rur-waves_rur-usd_rur')
ASK_DICT = {}
BID_DICT = {}
for pair in fivepairs:
    ASK_DICT[pair] = Ask_Price(fivepairs[pair], 0)
    BID_DICT[pair] = Bid_Price(fivepairs[pair], 0)
ASK_DICT['rur_rur'] = 1
BID_DICT['rur_rur'] = 1


res = requests.get('https://yobit.net/api/3/info') # получаем данные info
res_obj = json.loads(res.text) # переводим полученный текст в объект с данными
allpairs = []
cnt = 0
for pair in res_obj['pairs']:
    if pair.endswith('_rur'):
        allpairs.append(pair)
        cnt = cnt +1
print(cnt, 'пар')


for pair in allpairs:

    pbtc = pair.replace('_rur', '_btc')
    peth = pair.replace('_rur', '_eth')
    pdoge = pair.replace('_rur', '_doge')
    pwaves = pair.replace('_rur', '_waves')
    pusd =pair.replace('_rur', '_usd')
    this_pair_string = pbtc+'-'+peth+'-'+pdoge+'-'+pwaves+'-'+pusd+'-'+pair
    this_pair_info = GetInfo(this_pair_string)
    # Создаем справочник крайних ASK и BID для каждой из пяти валют
    this_pair_asks = {}
    this_pair_bids = {}
    for p in this_pair_info:
        it = p.split('_')
        this_pair_asks[p] = Decimal(inrurask(Ask_Price(this_pair_info[p], 0), it[1]+'_rur')).quantize(Decimal("1.00000000"))
        this_pair_bids[p] = Decimal(inrurbid(Bid_Price(this_pair_info[p], 0), it[1]+'_rur')).quantize(Decimal("1.00000000"))
    minaskpair = min(this_pair_asks, key=this_pair_asks.get)
    maxbidpair = max(this_pair_bids, key=this_pair_asks.get)
    minask = this_pair_asks[minaskpair]
    maxbid = this_pair_bids[maxbidpair]
    print(' ')
    print(minaskpair, 'ПРОДАЮТ:', minask)
    print(maxbidpair, 'ПОКУПАЮТ:', maxbid)
    if minask < maxbid and minask != 0: print('------------------------------------------------------ НАШЛАСЬ!!!')
