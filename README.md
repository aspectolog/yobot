# bot.py - YoBit spread bot
### Keep the first position in the spread.

#### Using:
1. Edit **cfg.py**
3. Make sure you have opened position in target pair.
4. Run this script:


    bot.py [Interval_in_sec] [coin]

Example:

    python3 bot.py 30 btc

If [coin] is not specified, will used **404_rur** pair by default.

**Warning! Working with Stop-file is breaking.**


Бот поддерживает позиции на покупку и продажу по крайним ценам спреда, если цены в коридоре, указанном в текстовом файле с именем монеты.

!-Значения в контрольном файле создаются криво. Необходимо пофиксить перед использованием-!

!-Не все исключения обрабатываются корректно-!

------------

## find.py - Поиск арбитражных пар.
Ищет прибыльные обменные цепочки. Пересчёт на рубли.

## fmaxspr.py
Поиск пар со спредом и объемом больше заданных.

## findmin.py
Поиск дешёвых пар.

## balance.py
Считает баланс аккаунта по реальным текущим ценам спроса и предложения.
