import yfinance as yf
import datetime
import pandas as pd
import pytz
import logging

logger = logging.getLogger(__name__)

def yfinanceGet():  # No lo uso. Solo para test
    symbols = []
    symbols.append('HEM24.CME')
    #symbols.append('HEN25.CME')
    #symbols.append('HEQ25.CME')
    
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

def dataframe_assign_tz (df_, tz_):
    try:
        df_.index = df_.index.tz_localize(tz_)
    except:
        logging.error ('Error al asignar TZ a Df')
    else:
        return df_
    
    try:
        df_.index = df_.index.tz_convert(tz_)
    except:
        logging.error ('Error al convertir el TZ de Df')
    else:
        return df_
    
    return df_


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
    data_output_vol_series = {}
    
    remoteTz = pytz.timezone("America/Chicago")

    if end_date_arg:
        if end_date_arg.tzinfo == None or end_date_arg.tzinfo.utcoffset(end_date_arg) == None:
            end_date_arg = remoteTz.localize(end_date_arg)    
        else:
            end_date_arg = end_date_arg.astimezone(remoteTz)
  
    for symbol in symbols:
        
        size = 1
        data_final = pd.DataFrame()
        data_final_1m = pd.DataFrame()
        data_final_1h = pd.DataFrame()
        data_final_1d = pd.DataFrame()
        
        if not end_date_arg:
            end_date = datetime.datetime.now()
            end_date = end_date.replace(hour = 0, minute = 0, second = 0, microsecond=0)
            end_date = remoteTz.localize(end_date)   
        else:
            end_date = end_date_arg

        start_date = end_date - datetime.timedelta(days=3)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        code_yf = symbol['code']
        if code_yf[-2].isnumeric():
            code_yf = code_yf + ".CME"
        else:
            decadeDigit = getCurrentDecadeDigit()
            code_yf = code_yf[:-1] + decadeDigit + code_yf[-1] + ".CME"
            
        while size > 0:
            logging.info ('Descargando (1m) %s desde %s a %s', symbol['code'], start_date, end_date) 
            data = yf.download(code_yf, end=end_date, start=start_date, interval="1m")
            data_final_1m = pd.concat([data, data_final_1m])
            size = data.size
            if size > 0:
                end_date = start_date
                start_date = start_date - datetime.timedelta(days=3)

        data_final_1m = dataframe_assign_tz (data_final_1m, 'America/Chicago')
    
        size = 1
        while size > 0:
            logging.info ('Descargando (1h) %s desde %s a %s', symbol['code'], start_date, end_date) 
            data = yf.download(code_yf, end=end_date, start=start_date, interval="1h")
            data_final_1h = pd.concat([data, data_final_1h])
            size = data.size
            if size > 0:
                end_date = start_date
                start_date = start_date - datetime.timedelta(days=3)

        data_final_1h = dataframe_assign_tz (data_final_1h, 'America/Chicago')
        
        size = 1
        while size > 0:
            logging.info ('Descargando (1d) %s desde %s a %s', symbol['code'], start_date, end_date) 
            data = yf.download(code_yf, end=end_date, start=start_date, interval="1d")
            data_final_1d = pd.concat([data, data_final_1d])
            size = data.size
            if size > 0:
                end_date = start_date
                start_date = start_date - datetime.timedelta(days=3)
        
        data_final_1d = dataframe_assign_tz (data_final_1d, 'America/Chicago')

        data_final = pd.concat([data_final_1d, data_final_1h])
        data_final = pd.concat([data_final, data_final_1m])
        
        data_final.index.names = ['timestamp']
        logging.info('\n%s', data_final)
        '''
        try:
            #data_final = data_final.tz_localize('America/Chicago')
            data_final.index = data_final.index.tz_localize('America/Chicago')
        except:
            logging.error('Error asignando el TZ', exc_info=True)
        
        logging.info('\n%s', data_final)
        '''
        try:
            data_output[symbol['code']] = data_final.resample('1h').agg({'Open': 'first','High':'max','Low':'min','Close':'last'}).ffill()
        except:
            logging.error('Error en resample de OCHL', exc_info=True)

        try:
            data_output_vol_series[symbol['code']] = data_final['Volume'].resample('1d').sum()
            #data_final_vol[symbol['code']] = pd.DataFrame({'timestamp':data_output_vol_series.index, 'Volume':data_output_vol_series.values})
        except:
            logging.error('Error en resample de Volume', exc_info=True)
        

        # Quito findes de semana, y horas fuera de mercado. 
        # Paso a TZ Madrid
        # Renombro las columnas
        data_output[symbol['code']] = data_output[symbol['code']][data_output[symbol['code']].index.dayofweek < 5].between_time('9:00','14:00')
        data_output[symbol['code']] = data_output[symbol['code']].tz_convert('Europe/Madrid')
        data_output[symbol['code']] = data_output[symbol['code']].rename(columns={"Open":"open", "Close":"close", "High":"high", "Low":"low"})

        data_output_vol_series[symbol['code']] = data_output_vol_series[symbol['code']][data_output_vol_series[symbol['code']].index.dayofweek < 5]
        data_output_vol_series[symbol['code']] = data_output_vol_series[symbol['code']].tz_convert('Europe/Madrid')

    if len (symbols) > 1:
        final_output = pd.DataFrame()
        final_output_vol = pd.DataFrame()
    
        for symbol in symbols:
            if final_output.empty:
                final_output = data_output[symbol['code']] * symbol['ratio']
            else:
                final_output += data_output[symbol['code']] * symbol['ratio']

            #if len(final_output_vol.index) == 0:
            #    final_output_vol.index = data_output_vol_series[symbol['code']].index
            final_output_vol[symbol['code']] = data_output_vol_series[symbol['code']]
    
        data_output[symbol_arg] = final_output[final_output.index >= final_output.first_valid_index()]
        data_output_vol_series[symbol_arg] = final_output_vol[final_output_vol.index >= final_output_vol.first_valid_index()].min(axis=1)
        #data_output_vol_series[symbol_arg] = final_output_vol.min(axis=1)
        
        

    return data_output, data_output_vol_series


def calcular_best_media ():
    df1_, df_vol = yfinanceGetDelta1h('HEM5')
    
    df_list = df1_['HEM5']['close'].to_list()

    step = 25
    init = round(min(df_list) * 100)
    end = round (max (df_list) * 100) + step

    print ('Max: ', str(max))
    print ('Min: ', str(min))
    
    cross_n = {}

    for level in range (init, end, step):
        print ('Evaluamos Level', str(level))

        cross_n[level] = 0
        # Primero vemos donde está el primero
        if df_list[0] > level:
            var = 1 # El primer valor está por encima del level 
        else:
            var = -1 # Está por debajo
        for value in df_list:
            nvalue = value * 100
            print ('.....valor: ', nvalue)
            if nvalue > level:
                lvar = 1 # El primer valor está por encima del level 
            else:
                lvar = -1 # Está por debajo
            if lvar != var:
                cross_n[level] += 1
                var = lvar

    


    return cross_n

