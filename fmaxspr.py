
##########################################################
# Поиск пар с максимальным спредом и приличными объемами.
##########################################################

import requests
import json
from decimal import Decimal

#############################
VOL = "2000"
FACTOR = "1.8"
#############################


# Получаем цены = list[str, str]
def GetInfo(pair):
    otvet = requests.get('https://yobit.net/api/3/depth/' + pair)
    data = json.loads(otvet.text)
    return data

def GetTicker(pair):
    otvet = requests.get('https://yobit.net/api/3/ticker/' + pair)
    data = json.loads(otvet.text)
    return data

    #Получаем i-ую от края цену
def Ask_Price(data, i):
    data["asks"] = data.get("asks", ["0", "0"])
    return Decimal(data["asks"][i][0]).quantize(Decimal("1.00000000"))
def Bid_Price(data, i):
    data["bids"] = data.get("bids", ["0", "0"])
    return Decimal(data["bids"][i][0]).quantize(Decimal("1.00000000"))

def Volume(data):
    data = data.get("vol")
    return Decimal(data).quantize(Decimal("1.00000000"))


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

cnt = 1
c = 0
pairstr = ''
for pair in allpairs:
    if cnt == 1:
        pairstr = pair
        cnt += 1
    elif cnt < 10:
        pairstr = pairstr + '-' + pair
        cnt += 1
    else:
        PriceData = GetInfo(pairstr)
        VolumeData = GetTicker(pairstr)
        for this_pair in PriceData:
            ap = Ask_Price(PriceData[this_pair], 0)
            bp = Bid_Price(PriceData[this_pair], 0)
            vl = Volume(VolumeData[this_pair])
            print(10*c, '\rProcess: {}'.format(this_pair), end='      ')
            if ap / bp > Decimal(FACTOR) and vl > Decimal(VOL):
                print(' ')
                print(this_pair, '::', ap, ' --- ', bp, ' --- Объем: ', vl)
        cnt = 1
        c += 1
