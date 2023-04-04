import yfinance as yf
import datetime
import pandas as pd

def yfinanceGet():
    symbols = []
    symbols.append('HEZ23.CME')
    symbols.append('HEG24.CME')
    symbols.append('HEJ24.CME')
    
    data_output_1m = {}
    data_output_1h = {}
    data_output_1d = {}
    
    for symbol in symbols:
        
        size = 1
        data_final_1m = pd.DataFrame()
        data_final_1h = pd.DataFrame()
        data_final_1d = pd.DataFrame()
        file = '../market/' + symbol + '.csv'
    
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=3)
            
        while size > 0:
            data = yf.download(symbol, end=end_date, start=start_date, interval="1m")
            data_final_1m = pd.concat([data, data_final_1m])
            size = data.size
            if size >0:
                end_date = start_date
                start_date = start_date - datetime.timedelta(days=3)
    
        size = 1
        while size > 0:
            data = yf.download(symbol, end=end_date, start=start_date, interval="1h")
            data_final_1h = pd.concat([data, data_final_1h])
            size = data.size
            if size >0:
                end_date = start_date
                start_date = start_date - datetime.timedelta(days=3)
        size = 1
        while size > 0:
            data = yf.download(symbol, end=end_date, start=start_date, interval="1d")
            data_final_1d = pd.concat([data, data_final_1d])
            size = data.size
            if size >0:
                end_date = start_date
                start_date = start_date - datetime.timedelta(days=3)
        
        data_output_1m[symbol] = data_final_1m
        data_output_1h[symbol] = data_final_1h
        data_output_1d[symbol] = data_final_1d
        #data_final.to_csv(file, mode='w')
        #data_output_1m[symbol].index[0]
        #data_output_1m[symbol].index[-1]

    return data_output_1m, data_output_1h, data_output_1d




