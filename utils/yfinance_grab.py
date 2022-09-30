import yfinance as yf
import datetime
import pandas as pd

symbols = []
symbols.append('HEM23.CME')
symbols.append('HEN23.CME')
symbols.append('HEQ23.CME')


for symbol in symbols:
    
    size = 1
    data_final = pd.DataFrame()
    file = '../market/' + symbol + '.csv'

    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=3)
        
    while size > 0:
        data = yf.download(symbol, end=end_date, start=start_date, interval="1m")
        data_final = pd.concat([data, data_final])
        size = data.size
        if size >0:
            end_date = start_date
            start_date = start_date - datetime.timedelta(days=3)

    size = 1
    while size > 0:
        data = yf.download(symbol, end=end_date, start=start_date, interval="1h")
        data_final = pd.concat([data, data_final])
        size = data.size
        if size >0:
            end_date = start_date
            start_date = start_date - datetime.timedelta(days=3)
    size = 1
    while size > 0:
        data = yf.download(symbol, end=end_date, start=start_date, interval="1d")
        data_final = pd.concat([data, data_final])
        size = data.size
        if size >0:
            end_date = start_date
            start_date = start_date - datetime.timedelta(days=3)

    data_final.to_csv(file, mode='w')


