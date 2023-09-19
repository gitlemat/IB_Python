import pandas as pd
import matplotlib.pyplot as plt
import utils
import os.path
import time
import datetime
import queue
import sys
import utils


import logging

logger = logging.getLogger(__name__)
UNSET_DOUBLE = sys.float_info.max


# data_args = {'gConId': gConId, 'BID': price2buy, 'ASK':price2sell, 'LAST':price2last, 'Symbol':lSymbol, 'timestamp':timestamp}

'''
# Añadir linea
newlineL =[{'gConId': 496647135 ,'timestamp': 1660674495, 'BID':103, 'ASK':102, 'LAST':101.7,'Symbol':'HEZ2'}]
df = pd.concat([df, pd.DataFrame.from_records(newlineL)], ignore_index=True)

# Borrar linea
index = df[df['timestamp']>1660674485].index
df.drop(index)

# dibujar
plt.rcParams.update({'font.size': 10, 'figure.figsize': (10, 8)}) 
df.plot(kind='scatter', x='timestamp', y='ASK', title='Titulo')
plt.show()
'''

class dbPandasAccount():
    #AccountType: INDIVIDUAL
    #accountId: DU5853276
    #Cushion: 0.99606
    #LookAheadNextChange: 1690825800
    #AccruedCash: 5173.46
    #AvailableFunds: 1944731.12
    #BuyingPower: 12964874.14
    #EquityWithLoanValue: 1954356.26
    #ExcessLiquidity: 1946747.00
    #FullAvailableFunds: 1944731.12
    #FullExcessLiquidity: 1946747.00
    #FullInitMarginReq: 9625.14
    #FullMaintMarginReq: 7700.11
    #GrossPositionValue: 0.00
    #InitMarginReq: 9625.14
    #LookAheadAvailableFunds: 1944731.12
    #LookAheadExcessLiquidity: 1946747.00
    #LookAheadInitMarginReq: 9625.14
    #LookAheadMaintMarginReq: 7700.11
    #MaintMarginReq: 7700.11
    #NetLiquidation: 1954447.11
    #TotalCashValue: 1949273.65

    def __init__(self, accountId, influxIC):

        timestamp = datetime.datetime.now()
        timestamp = utils.date2local (timestamp)
        
        self.dfAccountEvo_ = None
        self.influxIC_ = influxIC
        self.accountId_ = accountId
        self.last_refresh_db_ = timestamp
        self.toPrint = True

        self.dbReadInflux()
        
    def dbReadInflux(self):
        logging.debug  ('Leemos de influx y cargamos los dataframes')
        self.dfAccountEvo_ = self.influxIC_.influxGetAccountDataFrame (self.accountId_)
        if len (self.dfAccountEvo_) > 0:
            logging.debug ('Este es el Account DF:')
            logging.debug ('%s', self.dfAccountEvo_)
            logging.debug ('%s', self.dfAccountEvo_.index[-1])
            self.last_refresh_db_ = self.dfAccountEvo_.index[-1]
        else:
            timestamp = datetime.datetime.now()
            timestamp = utils.date2local (timestamp)
            self.last_refresh_db_ = timestamp - datetime.timedelta(hours=48) # Por poner algo

    def dbUpdateAddAccountData (self, data):
        
        keys_account = [
            'accountId', 'Cushion', 'LookAheadNextChange', 'AccruedCash', 
            'AvailableFunds', 'BuyingPower', 'EquityWithLoanValue', 'ExcessLiquidity', 'FullAvailableFunds',
            'FullExcessLiquidity','FullInitMarginReq','FullMaintMarginReq','GrossPositionValue','InitMarginReq',
            'LookAheadAvailableFunds','LookAheadExcessLiquidity','LookAheadInitMarginReq','LookAheadMaintMarginReq',
            'MaintMarginReq','NetLiquidation','TotalCashValue'
        ]
        logging.debug ('Actulizamos Account Data %s: %s', self.accountId_, data)

        try:
            lastone = self.dfAccountEvo_.iloc[-1].to_dict()
        except:     # self.dfAccountEvo_ es vacio. Se deja como incompleto para qie no escriba
            different = True
            for key in keys_account: # Todos los valores que no traiga, los pongo a None
                if key not in data:
                    data[key] = None
        else:
            different = False
            logging.debug ('Comparo con %s', lastone)
            for key in keys_account:  
                if key not in data:
                    if key in lastone: # Todos los valores que no tenga, los pillo de lastone, y si no None
                        data[key] = lastone[key]
                    else:
                        data[key] = None
                if key in lastone and (lastone[key] != data[key]):
                    different = True
                elif key not in lastone and data[key] != None:
                    different = True

        timestamp = datetime.datetime.now()
        timestamp = utils.date2local (timestamp)
        data['timestamp'] = timestamp

        newlineL = []
        newlineL.append (data)

        if different and (timestamp - self.last_refresh_db_ > datetime.timedelta(hours=24)):
            self.influxIC_.influxUpdateAccountData (self.accountId_, data)
            dfDelta = pd.DataFrame.from_records(newlineL)
            dfDelta.set_index('timestamp', inplace=True)
            #logging.info ('Escribo valor para %s: %s', self.symbol_, dfDelta)
            self.dfAccountEvo_ = pd.concat([self.dfAccountEvo_, dfDelta]) #, ignore_index=True
            self.toPrint = True
    '''
    def dbUpdateInfluxAccountData (self, data):
        keys_account = [
            'accountId', 'Cushion', 'LookAheadNextChange', 'AccruedCash', 
            'AvailableFunds', 'BuyingPower', 'EquityWithLoanValue', 'ExcessLiquidity', 'FullAvailableFunds',
            'FullExcessLiquidity','FullInitMarginReq','FullMaintMarginReq','GrossPositionValue','InitMarginReq',
            'LookAheadAvailableFunds','LookAheadExcessLiquidity','LookAheadInitMarginReq','LookAheadMaintMarginReq',
            'MaintMarginReq','NetLiquidation','TotalCashValue'
        ]
        
        records = []
        record = {}
        tags = {'accountId': self.accountId_}
        time = data['timestamp']
        time = utils.dateLocal2UTC (time)
        
        fields_influx = {}

        for key in keys_account:
            if key in data:
                if data[key] != None and data[key] != UNSET_DOUBLE:
                    fields_influx[key] = data[key]


        record = {
            "measurement": "account", 
            "tags": tags,
            "fields": fields_influx,
            "time": time,
        }

        records.append(record)

        if len(fields_influx) > 0:
            self.influxIC_.write_data(records, 'account')
    '''
    

class dbPandasStrategy():

    def __init__(self, symbol, strategyType, influxIC):
        self.dfExecs_ = None
        self.dfExecCount_ = None
        self.ExecsList = {} # Esta no es un pandas, pero viene bien dejarlo aqui
        self.ExecsPnL_ = {'avgPrice': 0, 'count': 0, 'PnL': 0} # Lo mismo, es mejor aqui

        self.symbol_ = symbol
        self.influxIC_ = influxIC
        self.strategyType = strategyType
        self.toPrint = True
        
        self.dbReadInflux()

        self.dbGetExecPnLInit()  # Alimentamos el self.ExecsPnL_

    def dbReadInflux(self):
        logging.debug  ('Leemos de influx y cargamos los dataframes')
        # ["_time", "ExecId", "PermId", "OrderId", "Quantity", "Side", "RealizedPnL", "Commission", "FillPrice"]
        self.dfExecs_ = self.influxIC_.influxGetExecDataFrame (self.symbol_, self.strategyType)
        self.dfExecCount_ = self.influxIC_.influxGetExecCountDataFrame (self.symbol_, self.strategyType)

    def dbGetExecsDataframeAll(self):
        return self.dfExecs_

    def dbGetExecsDataframeToday(self):
        #                                   OrderId  Quantity Side
        # timestamp                                               
        # 2022-12-28 20:05:39.169260+00:00     7866       1.0  BOT

        today = datetime.datetime.today()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        today = utils.date2local (today)

        ret = self.dfExecs_[(self.dfExecs_.index > today)]

        return ret

    def dbGetExecsDataframeYesterday(self):
        yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
        yesterdayInit = yesterday.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        yesterdayEnd = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=None)
        yesterdayInit = utils.date2local (yesterdayInit)
        yesterdayEnd = utils.date2local (yesterdayEnd)
        
        ret = self.dfExecs_[((self.dfExecs_.index > yesterdayInit) & (yesterdayEnd > self.dfExecs_.index))]

        return ret

    def dbGetExecCountToday(self):
        today = datetime.datetime.today()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        today = utils.date2local (today)

        ret = self.dfExecCount_[self.dfExecCount_.index ==  today]

        logging.debug("Las Exec count hoy: \n%s", self.dfExecCount_)
        if len(ret) > 0:
            return ret.iloc[-1]['ExecCount']
        
        return 0

    def dbGetExecCountAll(self):
        ret = self.dfExecCount_.sum(axis=0)['ExecCount']
        return ret

    def dbGetExecPnL(self):
        return self.ExecsPnL_


    def dbGetExecPnLInit(self):
        # ["_time", "ExecId", "PermId", "OrderId", "Quantity", "Side", "RealizedPnL", "Commission", "FillPrice"]
        logging.info('Llego aqui')

        for index, row in self.dfExecs_.iterrows():
            logging.info('Nuevo. FillPrice: %s. Qty: %s. Side: %s. Commission: %s', row['FillPrice'], row['Quantity'], row['Side'], row['Commission'])
            for i in range(int(row['Quantity'])):
                self.dbAddExecPnL(row)

    def dbAddExecPnL(self, row):
        count = self.ExecsPnL_['count']
        avgPrice = self.ExecsPnL_['avgPrice']
        tPnL = self.ExecsPnL_['PnL']

        if row['Side'] == 'BOT':
            new_count = count + 1
        else:
            new_count = count - 1

        new_tPnL = tPnL
        new_avgPrice = avgPrice

        # Lotes por contrato
        lotes_contrato = 400
        fillPrice = row['FillPrice'] * lotes_contrato

        qty = float(row['Quantity'])

        if new_count == 0:
            new_avgPrice = 0     
            if row['Side'] == 'BOT':
                new_tPnL = tPnL + avgPrice - fillPrice - row['Commission']/qty
            else:
                new_tPnL = tPnL + fillPrice - avgPrice - row['Commission']/qty
        elif new_count > 0:
            if row['Side'] == 'BOT':
                new_avgPrice = (avgPrice * abs(count) + fillPrice) / abs(new_count)
                new_tPnL = tPnL - row['Commission']/qty
            else:
                new_tPnL = tPnL + fillPrice - avgPrice - row['Commission']/qty
        elif new_count < 0:
            if row['Side'] == 'SLD':
                new_avgPrice = (avgPrice * abs(count) + fillPrice) / abs(new_count)
                new_tPnL = tPnL - row['Commission']/qty
            else:
                new_tPnL = tPnL + avgPrice - fillPrice - row['Commission']/qty
        avgPrice = new_avgPrice
        count = new_count
        tPnL = new_tPnL

        self.ExecsPnL_ = {'avgPrice': avgPrice, 'count': count, 'PnL': tPnL}
        logging.info('Actualizamos PnL en estrategia %s: %s', self.symbol_, self.ExecsPnL_)

    def dbAddExecToCount(self):
        today = datetime.datetime.today()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        today = utils.date2local (today)
        try:
            lastdate = self.dfExecCount_.index.max().to_pydatetime()
        except:
            lastdate = today - datetime.timedelta(days=3)

        if today == lastdate:
            self.dfExecCount_.iloc[-1]['ExecCount'] += 1
        else:
            data = {'timestamp': today, 'ExecCount': 1}
            newlineL = []
            newlineL.append(data)
            dfDelta = pd.DataFrame.from_records(newlineL)
            dfDelta.set_index('timestamp', inplace=True)
            self.dfExecCount_ = pd.concat([self.dfExecCount_, dfDelta])

    
    def dbAddCommissionsOrderFill(self, dataFlux):
        newlineL = []
        newlineL.append (dataFlux)
        dfDelta = pd.DataFrame.from_records(newlineL)
        dfDelta.set_index('timestamp', inplace=True)
        # OJJJJJOOOOOOO
        # Aqui hay que comprobar qye el ExecId no exista. Puede que IB lo mande dos veces
        self.dfExecs_ = pd.concat([self.dfExecs_, dfDelta]) #, ignore_index=True
        self.dbAddExecToCount() 
        self.dbAddExecPnL(dataFlux)
        self.dbUpdateInfluxCommission (dataFlux)

        self.toPrint = True

    def dbUpdateInfluxCommission (self, data):
        keys_comission = ['ExecId', 'PermId', 'OrderId', 'Quantity', 'Side', 'RealizedPnL', 'Commission', 'FillPrice']
        
        records = []
        record = {}
        tags = {'symbol': self.symbol_, 'strategy': self.strategyType}
        time = data['timestamp']
        time = utils.dateLocal2UTC (time)
        
        fields_influx = {}

        for key in keys_comission:
            if key in data:
                if data[key] != None and data[key] != UNSET_DOUBLE:
                    fields_influx[key] = data[key]


        record = {
            "measurement": "executions", 
            "tags": tags,
            "fields": fields_influx,
            "time": time,
        }

        records.append(record)

        if len(fields_influx) > 0:
            self.influxIC_.write_data(records, 'executions')


class dbPandasContrato():

    def __init__(self, symbol, influxIC):
        self.df_ = None
        self.dfcomp_ = None
        self.dfPnl_ = None
        self.dfVolume_ = None
        self.symbol_ = symbol
        self.influxIC_ = influxIC
        self.toSaveComp = False
        self.dateRanges = [] # aqui guardo el rango de fechas que he metido en pandas pero sin venir de influx. 
        self.toPrint = True
        self.toPrintPnL = True

        logging.debug  ('Leemos de influx y cargamos los dataframes')
        
        self.df_ = self.influxIC_.influxGetTodayDataFrame (self.symbol_)        
        self.dfcomp_ = self.influxIC_.influxGetOchlDataFrame (self.symbol_)
        self.dfPnl_ = self.influxIC_.influxGetPnLDataFrame (self.symbol_)

    def dbReadInfluxPrices(self):
        logging.debug  ('Leemos de influx y cargamos los dataframes por si estoy en competing')
        
        self.df_ = self.influxIC_.influxGetTodayDataFrame (self.symbol_)        

    def dbReadInfluxPricesComp(self):
        logging.debug  ('Leemos de influx y cargamos los dataframes de comp')
        
        self.dfcomp_ = self.influxIC_.influxGetOchlDataFrame (self.symbol_)

    def dbGetDataframeToday(self):
        #otime = self.df_.index[0]
        #otimeDT = otime.to_pydatetime()
        otimeDT = datetime.datetime.now()
        otimeDT = otimeDT.replace(hour=15, minute=40, second=0, microsecond=0, tzinfo=None)
        otimeDT = utils.date2local (otimeDT) # Para poder comparar
        
        #logging.info('Pandas: %s', self.df_.index)
        #logging.info('otimeDT: %s', otimeDT)
        ret = self.df_[(self.df_.index > otimeDT)]

        return ret

    def dbGetDataframeComp(self):
        return self.dfcomp_

    def dbGetFirstCompDate(self):
        a = self.dfcomp_.first_valid_index()
        b = self.df_.first_valid_index()

        if not a and not b:
            return None

        if not a:
            return b
        if not b:
            return a

        if a < b:
            return a
        else:
            return b
        
    def dbAddCompDataFrame (self, data_df):
        logging.info ('Lo que voy a añadir:\n%s', data_df)
        try:
            self.dfcomp_ = pd.concat([data_df, self.dfcomp_]) 
        except:
            logging.error ('Error añadiendo datos a dfcomp_')
            return None
        else:
            logging.info ('Lo que tengo ahora:\n%s', self.dfcomp_)

        self.toSaveComp = True

        start_date = data_df.index.min()
        end_date = data_df.index.max()

        rango = {'start': start_date, 'end': end_date}
        self.dateRanges.append(rango)
        logging.info('Añado fechas. Start: %s. End: %s', start_date, end_date)

        #Todo lo que se meta por aquí no está en influx. Hay que indicar las fechas.

    def dbGetLastPrices(self):
        lastPrices = {}
        lastPrices['ASK'] = None
        lastPrices['BID'] = None
        lastPrices['LAST'] = None
        lastPrices['ASK_SIZE'] = None
        lastPrices['BID_SIZE'] = None
        lastPrices['LAST_SIZE'] = None
        try:
            lastPrices = self.df_.iloc[-1]
        except:
            logging.error ('El df_ está vacio para %s', self.symbol_)
            lastPrices = {}
            lastPrices['ASK'] = None
            lastPrices['BID'] = None
            lastPrices['LAST'] = None
            lastPrices['ASK_SIZE'] = None
            lastPrices['BID_SIZE'] = None
            lastPrices['LAST_SIZE'] = None

        if not 'ASK' in lastPrices:
            lastPrices['ASK'] = None
        if not 'BID' in lastPrices:
            lastPrices['BID'] = None
        if not 'LAST' in lastPrices:
            lastPrices['LAST'] = None
        if not 'ASK_SIZE' in lastPrices:
            lastPrices['ASK_SIZE'] = None
        if not 'BID_SIZE' in lastPrices:
            lastPrices['BID_SIZE'] = None
        if not 'LAST_SIZE' in lastPrices:
            lastPrices['LAST_SIZE'] = None
            
        return (lastPrices)

    def dbGetLastPnL(self):
        lastPnL = {}
        lastPnL['dailyPnL'] = None
        lastPnL['realizedPnL'] = None
        lastPnL['unrealizedPnL'] = None

        try:
            lastRecord = self.dfPnl_.iloc[-1]
        except:
            logging.error ('El df_ esta vacio para %s', self.symbol_)
        else:
            if 'dailyPnL' in lastRecord:
                lastPnL['dailyPnL'] = lastRecord['dailyPnL']
            if 'realizedPnL' in lastRecord:
                lastPnL['realizedPnL'] = lastRecord['realizedPnL']
            if 'unrealizedPnL' in lastRecord:
                lastPnL['unrealizedPnL'] = lastRecord['unrealizedPnL']

        return (lastPnL)

        
    def dbUpdateAddPrices (self, data):
        
        keys_prices = ['BID', 'ASK', 'LAST', 'BID_SIZE', 'ASK_SIZE', 'LAST_SIZE']
        logging.debug ('Actulizamos %s: %s', self.symbol_, data)

        try:
            lastone = self.df_.iloc[-1].to_dict()
        except:     # self.df_ es vacio. Se deja como incompleto para qie no escriba
            different = True
            for key in keys_prices: # Todos los valores que no traiga, los pongo a None
                if key not in data:
                    data[key] = None
        else:
            different = False
            logging.debug ('Comparo con %s', lastone)
            for key in keys_prices:  
                if key not in data:
                    if key in lastone: # Todos los valores que no tenga, los pillo de lastone, y si no None
                        data[key] = lastone[key]
                    else:
                        data[key] = None
                if key in lastone and (lastone[key] != data[key]):
                    different = True
                elif key not in lastone and data[key] != None:
                    different = True

        timestamp = datetime.datetime.now()
        timestamp = utils.date2local (timestamp)
        data['timestamp'] = timestamp

        newlineL = []
        newlineL.append (data)

        if different:
            self.dbUpdateInfluxPrices (data)
            dfDelta = pd.DataFrame.from_records(newlineL)
            dfDelta.set_index('timestamp', inplace=True)
            #logging.info ('Escribo valor para %s: %s', self.symbol_, dfDelta)
            self.df_ = pd.concat([self.df_, dfDelta]) #, ignore_index=True
            self.toPrint = True

    def dbUpdateAddPnL (self, data):
 
        keys_pnl = ['dailyPnL','realizedPnL','unrealizedPnL']
        logging.debug ('Actulizamos con %s', data)

        logging.debug ('[Pandas] - Pandas data: %s', data) 

        try:
            logging.debug ('[Pandas] - Escribir data0: %s', self.dfPnl_) 
            lastone = self.dfPnl_.iloc[-1].to_dict()
        except:     # self.dfPnl_ es vacio. Se deja como incompleto para qie no escriba
            differentPnL = True
            for key in keys_pnl: # Todos los valores que no traiga, los pongo a None
                if key not in data:
                    data[key] = None
        else:
            differentPnL = False
            for key in keys_pnl:  
                if key not in data:
                    if key in lastone: # Todos los valores que no tenga, los pillo de lastone, y si no None
                        data[key] = lastone[key]
                    else:
                        data[key] = None
                if key in lastone and (lastone[key] != data[key]):
                    differentPnL = True
                elif key not in lastone and data[key] != None:
                    differentPnL = True

        timestamp = datetime.datetime.now()
        timestamp = utils.date2local (timestamp)
        data['timestamp'] = timestamp
            
        newlineL = []
        newlineL.append (data)

        if differentPnL:
            self.dbUpdateInfluxPnL (data)
            dfDelta = pd.DataFrame.from_records(newlineL)
            dfDelta.set_index('timestamp', inplace=True)
            self.dfPnl_ = pd.concat([self.dfPnl_, dfDelta])
            self.toPrintPnL = True

    def dbUpdateAddVolume(self, data):
        keys_pnl = ['Volume']
        today = datetime.datetime.today()
        today = utils.date2local (today)
        today_chicago = utils.date2Chicago (today)  # La hora de chicago es mas facil de usar
        today_chicago = today.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        today_chicago = utils.date2UTC (today_chicago)  # Para que todo en Influx tenga el mismo TZ
        try:
            lastdate = self.dfVolume_.index.max().to_pydatetime()
        except:
            lastdate = today_chicago - datetime.timedelta(days=3)

        data = {'timestamp': today_chicago, 'Volume': data['VOLUME']}
        self.dbUpdateInfluxVolume (data)
        if today_chicago == lastdate:
            self.dfVolume_.iloc[-1]['Volume'] = data['Volume']
        else:
            newlineL = []
            newlineL.append(data)
            dfDelta = pd.DataFrame.from_records(newlineL)
            dfDelta.set_index('timestamp', inplace=True)
            self.dfVolume_ = pd.concat([self.dfVolume_, dfDelta])


    def dbUpdateInfluxPnL (self, data):
        keys_pnl = ['dailyPnL','realizedPnL','unrealizedPnL']
        
        records = []
        record = {}
        tags = {'symbol': self.symbol_}
        time = data['timestamp']
        time = utils.dateLocal2UTC (time)
        
        fields_pnl = {}

        for key in keys_pnl:
            if key in data:
                fields_pnl[key] = data[key]


        record = {
            "measurement": "pnl", 
            "tags": tags,
            "fields": fields_pnl,
            "time": time,
        }
        records.append(record)

        if len(fields_pnl) > 0:
            self.influxIC_.write_data(records, 'pnl')

    def dbUpdateInfluxPrices (self, data):
        keys_prices = ['BID', 'ASK', 'LAST', 'BID_SIZE', 'ASK_SIZE', 'LAST_SIZE']

        records = []
        record = {}
        tags = {'symbol': self.symbol_}
        time = data['timestamp']
        time = utils.dateLocal2UTC (time)
        
        fields_prices = {}

        
        for key in keys_prices:
            if key in data:
                fields_prices[key] = data[key]

        record = {
            "measurement": "precios", 
            "tags": tags,
            "fields": fields_prices,
            "time": time,
        }
        records.append(record)

        #logging.info ('Escribo valor para %s: %s', self.symbol_, records)

        if len(fields_prices) > 0:
            self.influxIC_.write_data(records, 'precios')


    def dbUpdateInfluxCompPrices (self):

        pdcomp = None

        if not self.toSaveComp:
            return

        self.toSaveComp = False

        for lrange in self.dateRanges:
            lpdcomp = self.dfcomp_[lrange['start'] : lrange['end']]
            if not pdcomp:
                pdcomp = lpdcomp
            else:
                pdcomp = pd.concat([pdcomp, lpdcomp])

        if len(pdcomp) < 1:
            return

        pdcomp.sort_index(inplace=True)
        pdcomp.index.names = ['_time']
        pdcomp['symbol'] = self.symbol_

        record_params = {
            "type": "comp",
            "measurement": "precios", 
            "tags": "symbol",
        }

        #logging.info ('Escribo valor para %s: %s', self.symbol_, records)

        ret = self.influxIC_.write_dataframe(pdcomp, record_params)

        if not ret:
            self.toSaveComp = True
            logging.error ('Problema guardando las Comp en influx')
        else:
            self.dateRanges = []   # Borramos

    def dbUpdateInfluxVolume (self, data):
        keys_pnl = ['Volume']
        
        records = []
        record = {}
        tags = {'symbol': self.symbol_}
        time = data['timestamp']
        time = utils.date2UTC (time)
        
        fields_volume = {}

        for key in keys_pnl:
            if key in data:
                fields_volume[key] = data[key]


        record = {
            "measurement": "volume", 
            "tags": tags,
            "fields": fields_volume,
            "time": time,
        }
        records.append(record)

        if len(fields_volume) > 0:
            self.influxIC_.write_data(records, 'volume')

        


            
    
