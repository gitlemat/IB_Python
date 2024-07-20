import datetime
import pandas as pd
import pytz
import influxAPI
import logging
import utils
import pandasDB
import globales

def calcular_best_media_symbols (symbol_list, params):
    
    dfcross_all = pd.DataFrame(columns = ['level'])
    if symbol_list == None or len (symbol_list) < 1:
        return dfcross_all
    influxIC_ = influxAPI.InfluxClient()
    dfcross_all = pd.DataFrame(columns = ['level'])
    logging.info('%s', params)

    dataFamilies_ = globales.G_RTlocalData_.contractListPandas_.Families_

    symbol_list_total = []
    
    for symbol in symbol_list:
        if symbol in dataFamilies_:
            symbol_list_total += dataFamilies_[symbol]['symbols']
        else:
            symbol_list_total.append (symbol)

    for symbol in symbol_list_total:
        dfcross_n = calcular_best_media (symbol, influxIC_, params)
        dfcross_all = pandasDB.dbPandasConcat(dfcross_all,dfcross_n)

    # {'LEM23-2LEQ23+LEV23': {-100:23, -8:3,....}}
    dfcross_all.set_index('level', inplace=True)
    dfcross_all.sort_index(inplace=True)
    dfcross_all.interpolate(limit_direction='both', limit_area='inside', inplace=True)
    dfcross_all.fillna(0, inplace=True)
    dfcross_all['media'] = dfcross_all.mean(axis=1)
    logging.debug ('--------------')
    logging.debug ('--------------')
    logging.debug ('%s', dfcross_all)
    logging.debug ('--------------')
    return dfcross_all


def calcular_best_media (symbol, influxIC_, params):
    
    if 'distancia' in params:
        dist_min = params['distancia']
    else:
        dist_min = 0

    if 'delta_init' in params and params['delta_init'] != None:
        delta_init = params['delta_init']
    else:
        delta_init = 0

    if 'delta_end' in params and params['delta_end'] != None:
        delta_end = params['delta_end']
    else:
        delta_end = 0

    '''

    cl = utils.contractCode2list(symbol)

    ahora = datetime.datetime.now()
    decada = str(ahora.year)[-2]
    century = str(ahora.year)[:2]

    year_start = ahora.year
    year_stop = 0

    for contr in cl:
        code = contr['code']
        if not code[-2].isnumeric():
            code = code[:-1] + decada + code[-1:]

        try:
            year = int(century + code[-2:])
            logging.debug ('Year: %s', year)
            logging.debug ('Century: %s', century)
            logging.debug ('Code: %s', code)
        except:
            logging.error ('Error al sacar año de %s', code)
            continue

        if year < year_start:
            year_start = year
        if year > year_stop:
            year_stop = year

    year_start -=2

    symbolStart = datetime.datetime.strptime("01 January " + str(year_start), "%d %B %Y")
    symbolStop = datetime.datetime.strptime("31 December " + str(year_stop), "%d %B %Y")
    '''

    dfcross_n = pd.DataFrame(columns = ['level',symbol])
    dfcross_n.set_index('level', inplace=True)

    symbolStart, symbolStop = influxIC_.influxGetFirstLastRecordsDataFrame(symbol)

    if symbolStart == None or symbolStop == None:
        logging.error ('Resultado de fechas vacio')
        return dfcross_n
    
    symbolStart = utils.dateLocal2UTC (symbolStart)
    symbolStop = utils.dateLocal2UTC (symbolStop)

    symbolStart = symbolStart + datetime.timedelta(days=delta_init)
    symbolStop = symbolStop - datetime.timedelta(days=delta_end)

    df1_ = influxIC_.influxGetCloseValueDataFrame (symbol, symbolStart, symbolStop)
    df1Close_ = df1_['close']
    df_list = df1_['close'].to_list()

    logging.debug('%s', df1Close_)

    if len (df1Close_) == 0:
        logging.error ('Resultado vacio')
        return dfcross_n

    step = 10
    min_level = round(min(df1Close_) * 100)
    max_level = round (max (df1Close_) * 100) + step

    logging.info ('Max: %s', str(min_level))
    logging.info ('Min: %s', str(max_level))

    for level in range (min_level, max_level, step):
        logging.debug ('Evaluamos Level %s', str(level))
        kLevel = round ((level / 100), 2)
        cross_n = 0
        dist = 0
        dist_list = []
        # Primero vemos donde está el primero
        if df_list[0] > level:
            var = 1 # El primer valor está por encima del level 
        else:
            var = -1 # Está por debajo
        #for value in df_list:
        for index, value in df1Close_.items():
            nvalue = value * 100
            ldist = abs(nvalue - level) / 100
            if ldist > dist:
                dist = ldist
            logging.debug ('.....valor: %s', nvalue)

            if nvalue > level:
                lvar = 1 # El valor está por encima del level 
            else:
                lvar = -1 # Está por debajo

            if lvar != var:
                if dist >= dist_min:
                    cross_n += 1
                var = lvar
                dist_list.append (dist)  # De momento no hago nada con ello
                dist = 0
        record = {'level': kLevel, symbol: cross_n}
        #dfcross_n = dfcross_n._append(record, ignore_index=True)
        
        newlineL = []
        newlineL.append (record)
        dfDelta = pd.DataFrame.from_records(newlineL)
        #dfDelta.set_index('level', inplace=True)
        dfcross_n = pandasDB.dbPandasConcat(dfcross_n, dfDelta)
        
    logging.debug ('%s', dfcross_n)
    return dfcross_n