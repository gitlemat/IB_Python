import yfinance as yf
import datetime
import pandas as pd
import pytz
import logging

logger = logging.getLogger(__name__)

def yfinanceGet():  # No lo uso. Solo para test
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

def symbolList (contractCode):
    contractList = []
    if contractCode[0] != '+' and contractCode[0] != '-':
        contractCode = '+' + contractCode
    contractCode = contractCode.replace('-',',-')
    contractCode = contractCode.replace('+',',+')
    if contractCode[0] == ',':   # Va a pasar siempre
        contractCode = contractCode[1:]
    codesList = contractCode.split(',')

    for code in codesList:
        cont = {}
        if code[0] == '-':
            action = -1
        else:
            action = 1
        code = code[1:]
        if code[0].isnumeric():
            cont['ratio'] = int(code[0])
            code = code [1:]
        else:
            cont['ratio'] = 1
        cont['ratio'] = cont['ratio'] * action

        cont ['code'] = code
        contractList.append(cont)

    return contractList

def getCurrentDecadeDigit():
    hoy = datetime.date.today()
    return str(hoy.year)[-2]


def yfinanceGetDelta1h(symbol_arg, end_date_arg = None):
    
    symbols = symbolList (symbol_arg)
    
    data_output = {}
    
    remoteTz = pytz.timezone("America/Chicago")

    if end_date_arg:
        if end_date_arg.tzinfo == None or end_date_arg.tzinfo.utcoffset(end_date_arg) == None:
            end_date_arg = remoteTz.localize(end_date_arg)    
        else:
            end_date_arg = end_date_arg.astimezone(remoteTz)
  
    for symbol in symbols:
        
        size = 1
        data_final = pd.DataFrame()
        
        if not end_date_arg:
            end_date = datetime.datetime.now()
            end_date = end_date.replace(hour = 0, minute = 0, second = 0, microsecond=0)
            end_date = remoteTz.localize(end_date)   
        else:
            end_date = end_date_arg

        start_date = end_date - datetime.timedelta(days=3)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        code_yf = symbol['code']
        decadeDigit = getCurrentDecadeDigit()
        code_yf = code_yf[:-1] + decadeDigit + code_yf[-1] + ".CME"
            
        while size > 0:
            logging.info ('Descargando %s desde %s a %s', symbol['code'], start_date, end_date) 
            data = yf.download(code_yf, end=end_date, start=start_date, interval="1m")
            data_final = pd.concat([data, data_final])
            size = data.size
            if size > 0:
                end_date = start_date
                start_date = start_date - datetime.timedelta(days=3)
    
        size = 1
        while size > 0:
            logging.info ('Descargando %s desde %s a %s', symbol['code'], start_date, end_date) 
            data = yf.download(code_yf, end=end_date, start=start_date, interval="1h")
            data_final = pd.concat([data, data_final])
            size = data.size
            if size > 0:
                end_date = start_date
                start_date = start_date - datetime.timedelta(days=3)
        '''
        size = 1
        while size > 0:
            logging.info ('Descargando %s desde %s a %s', symbol['code'], start_date, end_date) 
            data = yf.download(code_yf, end=end_date, start=start_date, interval="1d")
            data_final = pd.concat([data, data_final])
            size = data.size
            if size > 0:
                end_date = start_date
                start_date = start_date - datetime.timedelta(days=3)
        '''

        data_final.index.names = ['timestamp']
        try:
            data_final = data_final.tz_localize('America/Chicago')
        except:
            pass
        
        try:
            data_output[symbol['code']] = data_final.resample('1h').agg({'Open': 'first','High':'max','Low':'min','Close':'last'}).ffill()
        except:
            logging.error('\n%s', data_final)

        # Quito findes de semana, y horas fuera de mercado. 
        # Paso a TZ Madrid
        # Renombro las columnas
        data_output[symbol['code']] = data_output[symbol['code']][data_output[symbol['code']].index.dayofweek < 5].between_time('9:00','14:00')
        data_output[symbol['code']] = data_output[symbol['code']].tz_convert('Europe/Madrid')
        data_output[symbol['code']] = data_output[symbol['code']].rename(columns={"Open":"open", "Close":"close", "High":"high", "Low":"low"})

    if len (symbols) > 1:
        final_output = pd.DataFrame()
    
        for symbol in symbols:
            if final_output.empty:
                final_output = data_output[symbol['code']] * symbol['ratio']
            else:
                final_output += data_output[symbol['code']] * symbol['ratio']
    
        data_output[symbol_arg] = final_output[final_output.index > final_output.first_valid_index()]

    return data_output



