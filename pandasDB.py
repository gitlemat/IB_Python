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
class dbPandasStrategy():

    def __init__(self, symbol, strategyType, influxIC):
        self.dfExecs_ = None
        self.dfExecCount_ = None
        self.ExecsList = {} # Esta no es un pandas, pero viene bien dejarlo aqui

        self.symbol_ = symbol
        self.influxIC_ = influxIC
        self.strategyType = strategyType
        self.toPrint = True
        self.toPrintPnL = True
        
        self.dbReadInflux()

    def dbReadInflux(self):
        logging.debug  ('Leemos de influx y cargamos los dataframes')
        self.dfExecs_ = self.influxIC_.influxGetExecDataFrame (self.symbol_, self.strategyType)
        self.dfExecCount_ = self.influxIC_.influxGetExecCountDataFrame (self.symbol_, self.strategyType)

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


    def dbAddExecOrder(self, data):
        logging.info ('[Execution (%s)] Actualizamos Exec Order de %s[%s]. ExedId: %s. Qty: %s, Side: %s, Type: %s', data['OrderId'],self.strategyType, self.symbol_, data['ExecId'], data['Quantity'], data['Side'], data['execSecType'])

        # Nos quedamos con la parte mas significativa del index
        index1 = data['ExecId'][:data['ExecId'].index('.')]
        rest = data['ExecId'][data['ExecId'].index('.')+1:]
        index2 = rest[:rest.index('.')]
        index = index1 + '.' + index2

        # Si el index recibido no está en la lista, lo añado
        if not index in self.ExecsList:
            self.ExecsList[index] = {}
            self.ExecsList[index]['realizadPnL'] = 0
            self.ExecsList[index]['Commission'] = 0
            self.ExecsList[index]['numLegs'] = data['numLegs']
            self.ExecsList[index]['legsDone'] = 0
            self.ExecsList[index]['Side'] = None
            self.ExecsList[index]['Quantity'] = 0
            self.ExecsList[index]['Cumulative'] = 0
            self.ExecsList[index]['lastFillPrice'] = 0
            self.ExecsList[index]['data'] = [] # Aquí guardamos cada una de las legs que me llegan, para luego recibir la commision
        
        # El qty/side lo pillo del index de la spread (me va a llegar uno de la spread y luego por cada leg)
        if data['contractSecType'] == data['execSecType']:
            self.ExecsList[index]['Side'] = data['Side']
            self.ExecsList[index]['Quantity'] = data['Quantity']
            self.ExecsList[index]['Cumulative'] = data['Cumulative']
        else:
            # Estos son los de cada leg. Aqui llenamos la lista, y la vaciamos en Commissiones
            self.ExecsList[index]['data'].append(data)

        if data['lastFillPrice'] != 0:
            self.ExecsList[index]['lastFillPrice'] = data['lastFillPrice']

    def dbAddCommissionsOrder(self, dataCommission):
        logging.debug ('[Comision (%s)] Actualizamos Commission en Estrategia %s: %s', self.symbol_, self.strategyType, dataCommission)
        #orden['params']['lastFillPrice']

        index1 = dataCommission.execId[:dataCommission.execId.index('.')]
        rest = dataCommission.execId[dataCommission.execId.index('.')+1:]
        index2 = rest[:rest.index('.')]
        index = index1 + '.' + index2

        dataExec = None
        if not index in self.ExecsList:
            logging.debug('[Comision (%s)] Esta comissionReport no es de esta strategia [%s]. ExecId: %s', self.symbol_, self.strategyType, dataCommission.execId)
            return False

        logging.info ('[Comision (%s)] Commission en Estrategia %s [%s]. Comission: %s. RealizedPnL: %s', dataCommission.execId, self.strategyType, self.symbol_, dataCommission.commission, dataCommission.realizedPNL)

        for exec in self.ExecsList[index]['data']:
            if  dataCommission.execId == exec['ExecId']:
                dataExec = exec
                break
        if not dataExec:
            logging.error ('[Comision (%s)] Comision sin tener la info de la Orden ExecId anteriormente. Estrategia %s [%s]', dataCommission.execId, self.strategyType, self.symbol_)
            return False

        self.ExecsList[index]['realizadPnL'] += dataCommission.realizedPNL
        self.ExecsList[index]['Commission'] += dataCommission.commission
        self.ExecsList[index]['legsDone'] += 1

        logging.info ('    Comision acumulada: [%s]', self.ExecsList[index]['Commission'])
        logging.info ('    RealizedPnL acumulada: [%s]', self.ExecsList[index]['realizadPnL'])

        self.ExecsList[index]['data'].remove(dataExec) # por si llegan dos comisiones al mismo Exec (no deberia)

        if self.ExecsList[index]['legsDone'] < dataExec['numLegs']:
            logging.info ('    El numero de legs de comision recibidas [%s] es inferior al del contrato [%s]', self.ExecsList[index]['legsDone'], dataExec['numLegs'])
            return True

        time = datetime.datetime.now()
        time = utils.date2local (time)
        dataFlux = {}
        dataFlux['timestamp'] = time
        dataFlux['ExecId'] = index + '01.01'
        dataFlux['OrderId'] = dataExec['OrderId']
        dataFlux['PermId'] = dataExec['PermId']
        dataFlux['Quantity'] = self.ExecsList[index]['Quantity'] 
        dataFlux['Side'] = self.ExecsList[index]['Side'] 
        dataFlux['RealizedPnL'] = self.ExecsList[index]['realizadPnL'] 
        dataFlux['Commission'] = self.ExecsList[index]['Commission'] 
        dataFlux['FillPrice'] = self.ExecsList[index]['lastFillPrice'] 
        # Aqui seguimos con le escritura a Flux
        # Y borrar todo el self.ExecsList[index]

        self.dbUpdateInfluxCommission (dataFlux)
        
        logging.info ('    Commission Order Finalizada [100%]')
        
        newlineL = []
        newlineL.append (dataFlux)
        dfDelta = pd.DataFrame.from_records(newlineL)
        dfDelta.set_index('timestamp', inplace=True)
        self.dfExecs_ = pd.concat([self.dfExecs_, dfDelta]) #, ignore_index=True
        self.dbAddExecToCount() 

        self.toPrint = True

        self.ExecsList.pop(index)

        return True

    def dbUpdateInfluxCommission (self, data):
        keys_comission = ['ExecId', 'PermId', 'OrderId', 'Quantity', 'Side', 'RealizedPnL', 'Commission', 'FillPrice']
        
        records = []
        record = {}
        tags = {'symbol': self.symbol_, 'strategy': self.strategyType}
        time = data['timestamp']
        time = utils.date2UTC (time)
        
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
        self.symbol_ = symbol
        self.influxIC_ = influxIC
        self.toPrint = True
        self.toPrintPnL = True

        self.dbReadInflux()

    def dbReadInflux(self):
        logging.debug  ('Leemos de influx y cargamos los dataframes')
        
        self.df_ = self.influxIC_.influxGetTodayDataFrame (self.symbol_)        
        self.dfcomp_ = self.influxIC_.influxGetOchlDataFrame (self.symbol_)
        self.dfPnl_ = self.influxIC_.influxGetPnLDataFrame (self.symbol_)

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
        return (lastPrices)

    def dbGetLastPnL(self):
        lastPnL = {}
        lastPnL['dailyPnL'] = None
        lastPnL['realizedPnL'] = None
        lastPnL['unrealizedPnL'] = None

        try:
            lastRecord = self.dfPnl_.iloc[-1]
        except:
            logging.error ('El df_ está vacio para %s', self.symbol_)
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


    def dbUpdateInfluxPnL (self, data):
        keys_pnl = ['dailyPnL','realizedPnL','unrealizedPnL']
        
        records = []
        record = {}
        tags = {'symbol': self.symbol_}
        time = data['timestamp']
        time = utils.date2UTC (time)
        
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
        time = utils.date2UTC (time)
        
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
        


            
    
