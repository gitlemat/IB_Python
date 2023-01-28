import pandas as pd
import matplotlib.pyplot as plt
import os.path
import time
import datetime
import pytz
import queue


import logging

logger = logging.getLogger(__name__)
utc=pytz.UTC


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

    def __init__(self, symbol, estrategia, influxIC):
        self.dfExecs_ = None
        self.dfExecCount_ = None

        self.symbol_ = symbol
        self.influxIC_ = influxIC
        self.estrategia_ = estrategia
        self.toPrint = True
        self.toPrintPnL = True
        self.ExecsList = {}

        self.dbReadInflux()

    def dbReadInflux(self):
        logging.debug  ('Leemos de influx y cargamos los dataframes')
        self.dfExecs_ = self.influxIC_.influxGetExecDataFrame (self.symbol_, self.estrategia_)
        self.dfExecCount_ = self.influxIC_.influxGetExecCountDataFrame (self.symbol_, self.estrategia_)

    def dbGetExecsDataframeToday(self):
        #                                   OrderId  Quantity Side
        # timestamp                                               
        # 2022-12-28 20:05:39.169260+00:00     7866       1.0  BOT

        today = datetime.datetime.today()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        
        ret = self.dfExecs_[(self.df_.index > today)]

        return ret

    def dbGetExecsDataframeYesterday(self):
        yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
        yesterdayInit = yesterday.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        yesterdayEnd = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=None)
        
        ret = self.dfExecs_[((self.df_.index > yesterdayInit) & (yesterdayEnd > self.df_.index))]

        return ret

    def dbGetExecCountToday(self):
        today = datetime.datetime.today()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)

        ret = self.dfExecCount_[self.dfExecCount_.index ==  today]
        if len(ret) > 0:
            return ret.iloc[-1]['ExecCount']
        
        return 0

    def dbGetExecCountAll(self):
        ret = self.dfExecCount_.sum(axis=0)['ExecCount']
        return ret

    def dbAddExecToCount(self):
        today = datetime.datetime.today()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        lastdate == self.dfExecCount_.index.max().to_pydatetime()

        if today == lastdate:
            self.dfExecCount_.iloc[-1]['ExecCount'] += 1
        else:
            data = {'timestamp': today, 'ExecCount': 1}
            newlineL = []
            newlineL.append(data)
            dfDelta = pd.DataFrame.from_records(newlineL)
            dfDelta.set_index('timestamp', inplace=True)
            self.dfExecCount_ =  pd.concat([self.dfExecCount_, dfDelta])
        
    def dbCheckIfExecIdInStrategy(self,ExecId ):
        index1 = ExecId[:ExecId.index('.')]
        rest = ExecId[ExecId.index('.')+1:]
        index2 = rest[:a2.rest('.')]
        index = index1 + '.' + index2

        if index in self.ExecsList:
            return True
        else:
            return False

    def dbAddExecOrder(self, data):
        logging.debug ('Actualizamos Exec Order %s[%s]: %s', self.estrategia_, self.symbol_, data)

        index1 = data['ExecId'][:data['ExecId'].index('.')]
        rest = data['ExecId'][data['ExecId'].index('.')+1:]
        index2 = rest[:rest.index('.')]
        index = index1 + '.' + index2

        if not index in self.ExecsList:
            self.ExecsList[index] = {}
            self.ExecsList[index]['realizadPnL'] = 0
            self.ExecsList[index]['Commission'] = 0
            self.ExecsList[index]['numLegs'] = data['numLegs']
            self.ExecsList[index]['legsDone'] = 0
            self.ExecsList[index]['Side'] = None
            self.ExecsList[index]['Quantity'] = 0
            self.ExecsList[index]['data'] = []
        
        if data['contractSecType'] == data['execSecType']:
            self.dbAddExecToCount()  # Mejor en comisionse
            self.ExecsList[index]['Side'] = data['Side']
            self.ExecsList[index]['Quantity'] = data['Quantity']
        else:
            # Aqui deberiamos llenar una queue, y vacier en Commissiones
            self.ExecsList[index]['data'].append(data)

    def dbAddCommissionsOrder(self, dataCommission):
        logging.debug ('Actualizamos Commission Order %s[%s]: %s', self.estrategia_, self.symbol_, dataCommission)

        index1 = dataCommission.execId[:dataCommission.execId.index('.')]
        rest = dataCommission.execId[dataCommission.execId.index('.')+1:]
        index2 = rest[:rest.index('.')]
        index = index1 + '.' + index2

        dataExec = None
        if not index in self.ExecsQueue:
            logging.error('Me ha llegado una comision sin tener la info de la Orden exec. ExecId: %s', dataCommission.execId)
            return

        for exec in self.ExecsQueue[index]:
            if  dataCommission.execId == exec['data'].execId:
                dataExec = exec
                break
        if not dataExec:
            logging.error('Me ha llegado una comision sin tener la info de la Orden exec. ExecId: %s', dataCommission.execId)
            return

        self.ExecsQueue[index]['realizadPnL'] += dataCommission.realizedPNL
        self.ExecsQueue[index]['Commission'] += dataCommission.commission
        self.ExecsQueue[index]['legsDone'] += 1

        if dataExec['legsDone'] < dataExec['numLegs']:
            return

        dataFlux = {}
        dataFlux['ExecId'] = index + '01.01'
        dataFlux['OrderId'] = dataExec['OrderId']
        dataFlux['PermId'] = dataExec['PermId']
        dataFlux['Quantity'] = self.ExecsQueue[index]['Quantity'] 
        dataFlux['Side'] = self.ExecsQueue[index]['Side'] 
        dataFlux['RealizedPnL'] = self.ExecsQueue[index]['realizadPnL'] 
        dataFlux['Commission'] = self.ExecsQueue[index]['Commission'] 
        # Aqui seguimos con le escritura a Flux
        # Y borrar todo el self.ExecsQueue[index]
        records = []
        record = {}
        tags = {'symbol': symbol, 'strategy': 'Pentagrama'}
        time = datetime.datetime.now()
    
        record = {
            "measurement": "executions", 
            "tags": tags,
            "fields": dataFlux,
            "time": time,
        }
        records.append(record)
    
        self.RTLocalData_.influxIC_.write_data(records)

        dataFlux.pop('ExecId', None)
        dataFlux.pop('PermId', None)
        
        newlineL = []
        newlineL.append (dataFlux)

        dfDelta = pd.DataFrame.from_records(newlineL)
        dfDelta.set_index('timestamp', inplace=True)
        self.dfExecs_ = pd.concat([self.dfExecs_, dfDelta]) #, ignore_index=True
        self.toPrint = True


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
        
        ret = self.df_[(self.df_.index > otimeDT)]

        return ret

    def dbGetDataframeComp(self):
        return self.dfcomp_

    def dbGetFileName(self):
        return 'market/' + self.symbol_ + time.strftime("_%y%m%d") + '.csv'

    def dbGetFilePnLName(self):
        return 'market/' + self.symbol_ + time.strftime("_%y%m%d") + '_pnl.csv'

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

        newlineL = []
        newlineL.append (data)

        if different:
            self.dbUpdateInfluxPrices (data)
            dfDelta = pd.DataFrame.from_records(newlineL)
            dfDelta.set_index('timestamp', inplace=True)
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
            self.influxIC_.write_data(records)

    def dbUpdateInfluxPrices (self, data):
        keys_prices = ['BID', 'ASK', 'LAST', 'BID_SIZE', 'ASK_SIZE', 'LAST_SIZE']
        
        '''
        records = [
            {
                "measurement": "cpu",
    	        "tags": {"core": "0"},
    	        "fields": {"temp": 25.3},
    	        "time": 1657729063
            },
        ]
        '''

        records = []
        record = {}
        tags = {'symbol': self.symbol_}
        time = data['timestamp']
        
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

        if len(fields_prices) > 0:
            self.influxIC_.write_data(records)
        


            
    
