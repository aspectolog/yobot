import hashlib
import hmac
import http.client
import json
import os
import sys
import time
import urllib
import subprocess
from decimal import Decimal
import requests
from cfg import *  # Читаем наш конфиг

if len(sys.argv) == 2:
    P = sys.argv[1]
    PAIR = P + '_rur'
elif len(sys.argv) == 3:
    P = sys.argv[2]
    PAIR = P + '_rur'
    time.sleep(int(sys.argv[1]))
else:
    PAIR = '404_rur'
    P = '404'

# Парсим наш конфиг
STOP_FILE += P
SELLSPREAD = Decimal(SELLSPREAD)
BIDSPREAD = Decimal(BIDSPREAD)

# Создаем nonce, если его нет
if not os.path.exists(nonce_file):
    with open(nonce_file, "w") as out:
        out.write('1')


# Всплывашка
def sendmess(message):
    subprocess.Popen(['notify-send', '-t', '300000', P, message])
    return


# Получаем цены = list[str, str]
def getinfo():
    ERR = True
    cnt = 0
    while ERR and cnt < 3:
        cnt = cnt + 1
        otvet = requests.get('https://yobit.net/api/3/depth/' + PAIR)
        try:
            data = json.loads(otvet.text)
            ERR = False
            return data
        except Exception:
            ERR = True
            print ('Ошибка. Повторяем запрос...')
#            msg = 'Ошибка анализа возвращаемых данных, получена строка'
#            sendmess(msg)
            time.sleep(3)


# Будем перехватывать все сообщения об ошибках с биржи
class YobitException(Exception):
    pass


def call_api(**kwargs):
    ERR = True
    cnt = 0
    while ERR and cnt < 3:
        cnt = cnt + 1
        # При каждом обращении к торговому API увеличиваем счетчик nonce на единицу
        with open(nonce_file, 'r+') as inp:
            nonce = int(inp.read())
            inp.seek(0)
            inp.write(str(nonce + 1))
            inp.truncate()
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
        conn = http.client.HTTPSConnection("yobit.net", timeout=90)
        conn.request("POST", "/tapi/", payload, headers)
        response = conn.getresponse().read()
        conn.close()
        try:
            obj = json.loads(response.decode('utf-8'))
            if 'error' in obj and obj['error']:
                ERR = True
                raise YobitException(obj['error'])
            ERR = False
            return obj

        except json.decoder.JSONDecodeError:
            ERR = True
#            msg = 'Ошибка анализа возвращаемых данных, получена строка'
#            sendmess(msg)
            print('Ошибка. Повторяем запрос...')
            time.sleep(3)

def CancelOrder(id):
    ERR = True
    cnt = 0
    while ERR and cnt < 5:
        cnt = cnt + 1
        try:
            print('Отменяем ордер...')
            call_api(method="CancelOrder", order_id=id)
            ERR = False
        except YobitException as e:
            ERR = True
            print("Облом:", e)
            print('Ошибка. Повторяем запрос...')
            time.sleep(3)
            


def MakeBuyOrder(price, amnt):
    ERR = True
    cnt = 0
    while ERR and cnt < 5:
        cnt = cnt + 1
        try:
            print('Создаем ордер на покупку...')
            call_api(method="Trade", pair=PAIR, type="buy", rate=price, amount=amnt)
            ERR = False
        except YobitException as e:
            ERR = True
            print("Облом:", e)
            print('Ошибка. Повторяем запрос...')
            time.sleep(3)


def MakeSellOrder(price, amnt):
    ERR = True
    cnt = 0
    while ERR and cnt < 5:
        cnt = cnt + 1
        try:
            print('Создаем ордер на продажу...')
            call_api(method="Trade", pair=PAIR, type="sell", rate=price, amount=amnt)
            ERR = False
        except YobitException as e:
            print("Облом:", e)
            print('Ошибка. Повторяем запрос...')
            time.sleep(3)


# Получаем i-ую от края цену
def Ask_Price(i):
    return Decimal(PriceData["asks"][i][0]).quantize(Decimal("1.00000000"))


def Bid_Price(i):
    return Decimal(PriceData["bids"][i][0]).quantize(Decimal("1.00000000"))


def Ask_Amount(i):
    return Decimal(PriceData["asks"][i][1]).quantize(Decimal("1.00000000"))


def Bid_Amount(i):
    return Decimal(PriceData["bids"][i][1]).quantize(Decimal("1.00000000"))


###############################################################################################################


BuyOrderVol = Decimal("0")
SellOrderVol = Decimal("0")

while True:
    interval = INTERVAL
    print(' ')
    print('=======================================================================')
    print('                              ', P)
    print('=======================================================================')
    print(' ')

    # Получаем один раз цены огромным массивом, дальше работаем с ним.
    PriceData = getinfo()[PAIR]

    # TODO: Пофиксить работу со стопценами и стопфайлом. Бред кошачий.
    # Создаем стоп-цены, если нет
    if not os.path.exists(STOP_FILE):
        with open(STOP_FILE, "w") as file:
            file.write(str((Bid_Price(0) + (Bid_Price(0) * SELLSPREAD)).quantize(Decimal("1.00000000"))) + '\n')
            file.write(str((Ask_Price(0) / (BIDSPREAD + 1)).quantize(Decimal("1.00000000"))))

    # Получаем стоп-цены
    with open(STOP_FILE, 'r+') as file:
        Stop_Sell_Price = Decimal(file.readline()).quantize(Decimal("1.00000000"))
        Stop_Bid_Price = Decimal(file.readline()).quantize(Decimal("1.00000000"))

    print("Стоп-цена на продажу: ", Stop_Sell_Price)
    print("Стоп-цена на покупку: ", Stop_Bid_Price)

    print('-' * 100)
    print('ASK(0): %-14s' % str(Ask_Price(0)),
          '%-20s' % str((Ask_Amount(0) * Ask_Price(0)).quantize(Decimal("1.00000000"))),
          '|     BID(0): %-15s' % str(Bid_Price(0)), (Bid_Amount(0) * Bid_Price(0)).quantize(Decimal("1.00000000")))
    print('ASK(1): %-14s' % str(Ask_Price(1)),
          '%-20s' % str((Ask_Amount(1) * Ask_Price(1)).quantize(Decimal("1.00000000"))),
          '|     BID(1): %-15s' % str(Bid_Price(1)), (Bid_Amount(1) * Bid_Price(1)).quantize(Decimal("1.00000000")))
    print('-' * 100)

    try:
        print('Получаем список активных ордеров...')

        active_orders = (call_api(method="ActiveOrders", pair=PAIR))
        there_is_order = False
        try:
            orders = active_orders['return']
            for k in orders:
                order_key = k
                order = orders[order_key]

                # ПРОДАЖА

                if order['type'] == 'sell':
                    there_is_order = True
                    Order_Rate = Decimal(order['rate']).quantize(Decimal("1.00000000"))
                    Order_Amount = Decimal(order['amount']).quantize(Decimal("1.00000000"))
                    print('-------------------------------------')
                    print('НАЙДЕН ОРДЕР SELL:', order_key)
                    print('ЦЕНА:', Order_Rate)
                    print('КОЛИЧЕСТВО:', Order_Amount)
                    print('СУММА:', (Order_Rate * Order_Amount).quantize(Decimal("1.00")), 'р.')
                    print('-------------------------------------')
                    if SellOrderVol != Decimal("0") and Order_Amount != SellOrderVol:
                        msg = 'Продано на сумму ' + str(((SellOrderVol - Order_Amount) * Order_Rate).quantize(Decimal("1.00"))) + ' р.'
                        sendmess(msg)
                    SellOrderVol = Order_Amount

                    if Ask_Price(0) < Order_Rate:  # Если текущая цена ниже нашей

                        if Ask_Price(0) > Stop_Sell_Price:  # Проверяем спред

                            New_Price = Ask_Price(0) - Decimal("0.00000001")
                            print('-' * 50)
                            CancelOrder(order_key)
                            print('-' * 50)
                            MakeSellOrder(New_Price, Order_Amount)
                            print('-' * 50)
                            print('     ----<( КОНКУРЕНТ. Цена ПРОДАЖИ ПОНИЖЕНА! Новая цена:', New_Price, 'на сумму',
                                  (New_Price * Order_Amount).quantize(Decimal("1.00")), 'р.', ' )>----')
                            print('-' * 50)

                        else:
                            msg = 'достигли Стоп-цены по продаже! Invest Mode. Ордер оставлен на цене ' + str(Order_Rate) + ' в размере ', str((Order_Rate * Order_Amount).quantize(Decimal("1.00"))) + ' р.'
                            print(msg)
                            sendmess(msg)

                    # Если текущая цена выше нашей больше чем на пункт и на нашей цене нет ордеров
                    elif Ask_Price(1) - Order_Rate > Decimal("0.00000001") and (Ask_Amount(0) - Order_Amount < Decimal(
                            "0.00000002")):

                        if Ask_Price(1) > Stop_Sell_Price:  # Проверяем спред

                            New_Price = Ask_Price(1) - Decimal("0.00000001")
                            print('=' * 50)
                            CancelOrder(order_key)
                            print('=' * 50)
                            MakeSellOrder(New_Price, Order_Amount)
                            print('=' * 50)
                            print('     ----<( ЗБС! Цена ПРОДАЖИ повышена! Новая цена:', New_Price, 'на сумму',
                                  (New_Price * Order_Amount).quantize(Decimal("1.00")), 'р.', ' )>----')

                        else:
                            msg = 'Достигли Стоп-цены по продаже! Invest Mode. Ордер оставлен на цене ' + str(Order_Rate) + ' в размере ' + str((Order_Rate * Order_Amount).quantize(Decimal("1.00"))) + ' р.'
                            print(msg)
                            sendmess(msg)

                    else:
                        print('     ----<( Ордер на продажу оставлен на цене', order['rate'], 'в размере',
                              (Order_Rate * Order_Amount).quantize(Decimal("1.00")), 'р.', ' )>----')

                # ПОКУПКА

                elif order['type'] == 'buy':
                    there_is_order = True
                    Order_Rate = Decimal(order['rate']).quantize(Decimal("1.00000000"))
                    Order_Amount = Decimal(order['amount']).quantize(Decimal("1.00000000"))
                    print('-------------------------------------')
                    print('НАЙДЕН ОРДЕР BUY:', order_key)
                    print('ЦЕНА:', Order_Rate)
                    print('КОЛИЧЕСТВО:', Order_Amount.quantize(Decimal("1.00000000")))
                    print('СУММА:', (Order_Rate * Order_Amount).quantize(Decimal("1.00")), 'р.')
                    print('-------------------------------------')
                    if BuyOrderVol != Decimal("0") and Order_Amount != BuyOrderVol:
                        msg = 'Куплено на сумму ' + str(((BuyOrderVol - Order_Amount) * Order_Rate).quantize(Decimal("1.00"))) + ' р.'
                        sendmess(msg)
                    BuyOrderVol = Order_Amount

                    if Bid_Price(0) > Order_Rate:  # Если текущая цена выше нашей
                        if Bid_Price(0) < Stop_Bid_Price:   # но меньше стоп-цены

                            New_Price = Bid_Price(0) + Decimal("0.00000001")
                            print('-' * 50)
                            CancelOrder(order_key)
                            print('-' * 50)
                            MakeBuyOrder(New_Price, Order_Amount)
                            print('-' * 50)
                            print('     ----<( КОНКУРЕНТ. Цена ПОКУПКИ ПОВЫШЕНА! Новая цена:', New_Price, 'на сумму',
                                  (New_Price * Order_Amount).quantize(Decimal("1.00")), 'р.', ' )>----')
                            print('-' * 50)

                        else:
                            msg = 'ВНИМАНИЕ! Текущая цена ПОКУПКИ выше Стоп-цены! Нахуй надо! Ордер оставлен на цене ' + str(Order_Rate) + ' в размере ' + str((Order_Rate * Order_Amount).quantize(Decimal("1.00"))) + ' р.'
                            print(msg)
                            sendmess(msg)

                    elif Order_Rate - Bid_Price(1) > Decimal("0.00000001") and (Bid_Amount(0) - Order_Amount < Decimal(
                            "0.00000002")):  # Если текущая цена ниже нашей больше чем на пункт и на нашей цене нет ордеров
                        if Bid_Price(1) < Stop_Bid_Price:  # Проверяем стоп-цену, на всякий

                            New_Price = Bid_Price(1) + Decimal("0.00000001")
                            print('=' * 50)
                            CancelOrder(order_key)
                            print('=' * 50)
                            MakeBuyOrder(New_Price, Order_Amount)
                            print('=' * 50)
                            print('     ----<( ЗБС! Цена ПОКУПКИ понижена! Новая цена:', New_Price, 'на сумму',
                                  (New_Price * Order_Amount).quantize(Decimal("1.00")), 'р.', ' )>----')

                        else:
                            msg = 'ВНИМАНИЕ! Превысили Стоп-цену покупки! Ордер оставлен на цене ' + str(Order_Rate) + ' в размере ' + str((Order_Rate * Order_Amount).quantize(Decimal("1.00"))) + ' р.'
                            print(msg)
                            sendmess(msg)

                    else:
                        print('     ----<( Ордер на покупку оставлен на цене', order['rate'], 'в размере',
                              (Order_Rate * Order_Amount).quantize(Decimal("1.00")), 'р.', ' )>----')

            if not there_is_order:
                msg = 'ОРДЕРОВ НЕТ!'
                print(msg)
                sendmess(msg)

                quit()

        except Exception:
            msg = 'Ошибка или ОРДЕРОВ НЕТ!'
            print(msg)
            sendmess(msg)
            break

    except YobitException as e:
        print("Облом:", e)
        interval = 3
    time.sleep(interval)
