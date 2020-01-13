
######################################################################
# Поиск дешёвых монет
######################################################################

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


res = requests.get('https://yobit.net/api/3/info') # получаем данные info
res_obj = json.loads(res.text) # переводим полученный текст в объект с данными
allpairs = []
cnt = 0
for pair in res_obj['pairs']:
    if pair.endswith('_rur'):
        allpairs.append(pair)
        cnt = cnt +1
print(cnt, 'пар')

cnt = 0
for pair in allpairs:
    try:
        cnt = cnt + 1
        this_pair_info = GetInfo(pair)
        thisprice = Decimal(Ask_Price(this_pair_info[pair], 0)).quantize(Decimal("1.00000000"))
        print('\rProcess: {} {}'.format(str(cnt), pair), end='     ')
        if thisprice < Decimal("0.0009") and thisprice > Decimal("0"):
            print(' ')
            print(pair, thisprice)
    except:
        continue
#    if minask < maxbid and minask != 0: print('------------------------------------------------------ НАШЛАСЬ!!!')
