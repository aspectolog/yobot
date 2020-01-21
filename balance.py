
######################################################################################################
# Переводит все монеты портфеля с ненулевым балансом в рубли по текущим ценам покупки и продажи.
# Подсчитывает ПРАВДИВУЮ полную текущую стоимость портфеля в рублях.
######################################################################################################

import os
import urllib, http.client
import hmac, hashlib
import requests
import json
from decimal import Decimal

from cfg import *

SELLSPREAD = Decimal(SELLSPREAD)
BIDSPREAD = Decimal(BIDSPREAD)

if not os.path.exists(nonce_file):
    with open(nonce_file, "w") as out:
        out.write('1')

# Получаем цены = list[str, str]
def GetInfo(pair):
    otvet = requests.get('https://yobit.net/api/3/depth/'+pair)
    data = json.loads(otvet.text)
    return data


class YobitException(Exception):
    pass

def call_api(**kwargs):
    # При каждом обращении к торговому API увеличиваем счетчик nonce на единицу
    with open(nonce_file, 'r+') as inp:
        nonce = int(inp.read())
        inp.seek(0)
        inp.write(str(nonce + 1))
        inp.truncate()
    print("Счетчик: ", nonce)

    payload = {'nonce': nonce}

    if kwargs:
        payload.update(kwargs)
    payload = urllib.parse.urlencode(payload)

    H = hmac.new(key=SECRET, digestmod=hashlib.sha512)
    H.update(payload.encode('utf-8'))
    sign = H.hexdigest()

    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Key": TRADE_KEY,
               "Sign": sign}
    conn = http.client.HTTPSConnection("yobit.net", timeout=60)
    conn.request("POST", "/tapi/", payload, headers)
    response = conn.getresponse().read()

    conn.close()

    try:
        obj = json.loads(response.decode('utf-8'))

        if 'error' in obj and obj['error']:
            raise YobitException(obj['error'])
        return obj
    except json.decoder.JSONDecodeError:
        raise YobitException('Ошибка анализа возвращаемых данных, получена строка', response)


    #Получаем i-ую от края цену
def Ask_Price(data, i):
    try:
        result = Decimal(data["asks"][i][0]).quantize(Decimal("1.00000000"))
    except:
        result = Decimal("0").quantize(Decimal("1.00000000"))
    return result


def Bid_Price(data, i):
    try:
        result = Decimal(data["bids"][i][0]).quantize(Decimal("1.00000000"))
    except:
        result = Decimal("0").quantize(Decimal("1.00000000"))
    return result

    ###############################################################################################################


asksumm = 0
bidsumm = 0
count = 0
pair = ''
amount = 0
paircount = 0
five_pair = {}
balances = call_api(method="getInfo")['return']['funds']
for h in balances:
    if Decimal(balances[h]) != 0 and h != 'yovi' and h != CURRENCY:
        paircount += 1
        five_pair[h + '_' + CURRENCY] = Decimal(balances[h]).quantize(Decimal("1.00000000"))
        if count == 0:
            pair = h + '_' + CURRENCY
            count += 1
        elif count < 10:
            pair = pair + '-' + h + '_' + CURRENCY
            count += 1
        else:
            PriceData = GetInfo(pair)
            for this_pair in PriceData:
                bidamount = (five_pair[this_pair] * Bid_Price(PriceData[this_pair], 0)).quantize(Decimal("1.00000000"))
                askamount = (five_pair[this_pair] * Ask_Price(PriceData[this_pair], 0)).quantize(Decimal("1.00000000"))
                print(this_pair, ' = ', askamount.quantize(Decimal("1.0000")), '        ', bidamount.quantize(Decimal("1.0000")))
                bidsumm = bidsumm + bidamount
                asksumm = asksumm + askamount
            count = 0
            five_pair.clear()
if count > 0:
    PriceData = GetInfo(pair)
    for this_pair in PriceData:
        bidamount = (five_pair[this_pair] * Bid_Price(PriceData[this_pair], 0)).quantize(Decimal("1.00000000"))
        askamount = (five_pair[this_pair] * Ask_Price(PriceData[this_pair], 0)).quantize(Decimal("1.00000000"))
        print(this_pair, ' = ', askamount.quantize(Decimal("1.0000")), '        ', bidamount.quantize(Decimal("1.0000")))
        bidsumm = bidsumm + bidamount
        asksumm = asksumm + askamount

print('__________________________________________________________________________')
print('ИТОГО ВЕСЬ ПОРТФЕЛЬ ПО ЦЕНЕ ПРЕДЛОЖЕНИЯ:', asksumm.quantize(Decimal("1.0000")))
print('ИТОГО ВЕСЬ ПОРТФЕЛЬ ПО ЦЕНЕ СПРОСА:', bidsumm.quantize(Decimal("1.0000")))
print('ВСЕГО ПАР:', paircount)

