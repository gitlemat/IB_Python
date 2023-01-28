import pandas as pd
import matplotlib.pyplot as plt
import os.path
import time
import datetime

import logging

logger = logging.getLogger(__name__)


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

class dbPandas():

    def __init__(self, symbol, influxIC):
        self.file_path_csv_ = None
        self.file_path_csvPnL_ = None
        self.df_ = None
        self.dfcomp_ = None
        self.dfPnl_ = None
        self.symbol_ = symbol
        self.influxIC_ = influxIC
        self.toPrint = True
        self.toPrintPnL = True

        self.dbInitFile ()

    def dbInitFile (self):
        self.dbFileCheck()
        self.dbReadAllFiles()
        self.dbReadInflux()

    def dbReadInflux(self):
        logging.debug  ('Leemos de influx y cargamos los dataframes')
        
        self.df_ = self.influxIC_.influxGetTodayDataFrame (self.symbol_)        
        self.dfcomp_ = self.influxIC_.influxGetOchlDataFrame (self.symbol_)

    def dbReadAllFiles(self):
        path = 'market/'
        self.df_ = None
        self.dfcomp_ = pd.DataFrame(columns = ['timestamp','open','high','low','close'])
        logging.debug  ('Leer todos los ficheros')

        bSegundoLeido = False
        nReadLength = 0
        todaystr = time.strftime("%y%m%d")
        for i in sorted(os.listdir(path), reverse=True):
            filename = os.path.join(path,i)
            
            if os.path.isfile(filename) and i.startswith(self.symbol_+'_'):
                logging.debug  ('Analizamos %s', filename)
                if i.endswith ('_pnl.csv'): # Los de pnl
                    datefile = i[-14:-8]
                    if datefile == todaystr:
                        self.dfPnl_ = pd.read_csv (filename, parse_dates=['timestamp'], index_col=0)    
                        logging.debug  ('     .. es pnl')
                elif i.endswith ('_comp.csv'): # Los comprimidos los cargo todos
                    logging.debug  ('     .. es comprimido')
                    df_new = pd.read_csv (filename, parse_dates=['timestamp'], index_col=0)
                    self.dfcomp_ = pd.concat([self.dfcomp_, df_new])
                else:  # Los no comprimidos, solo hoy y el antyerior no vacio, por si estamos a mitad del dia
                    datefile = i[-10:-4]
                    if datefile == todaystr or bSegundoLeido == False:
                        logging.debug  ('     .. es el no comprimido de hoy, o de undia anteriro para tener un minimo')
                        df_new = pd.read_csv (filename, parse_dates=['timestamp'])
                        if 'gConId' in df_new:     # Asumo que si lo tiene, es formto viejo
                            df_new.set_index('timestamp', inplace=True)
                            df_new.drop(['gConId','Symbol'], axis =1, inplace=True)
                        if 'timestamp' in df_new:     # no he podido indicar que e index_col=0 por el tema de los viejos
                            df_new.set_index('timestamp', inplace=True)
                        if 'dailyPnL' in df_new:     # Asumo que si lo tiene, es formto viejo
                            df_new.drop(['dailyPnL','realizedPnL','unrealizedPnL'], axis =1, inplace=True)
                        self.df_ = pd.concat([self.df_, df_new])
                        nReadLength += len(df_new.index)
                        if nReadLength > 10:
                            bSegundoLeido = True
        

        self.df_ = self.df_.sort_values(by=['timestamp']) # , ignore_index=True
        self.dfcomp_ = self.dfcomp_.sort_values(by=['timestamp']) # El comp si tiene index
        self.dfPnl_ = self.dfPnl_.sort_values(by=['timestamp'])


        logging.debug  ('--------------------')
        logging.debug  (self.symbol_)
        logging.debug  (self.df_)


    def dbGetDataframeToday(self):
        otime = self.df_.index[0]
        otimeDT = otime.to_pydatetime()

        otimeDT = otimeDT.replace(hour=15, minute=40, second=0, microsecond=0)
        
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


    def dbCompressClosedFiles (self):
        path = 'market/'
        dirlist = os.listdir(path)
        logging.info  ("Mirando si hay que comprimir")
        for i in dirlist:
            filename = os.path.join(path,i)
            i_comp = i[:-4] + '_comp.csv'
            filename_comp = os.path.join(path,i_comp)
            if os.path.isfile(filename) and filename != self.file_path_csv_ and i.startswith(self.symbol_+'_') and (not i.endswith ('_comp.csv')) and (not i.endswith ('_pnl.csv')) and (not i_comp in dirlist): # Fichero de este simbolo que no esta comprimido
                #logging.info  ("Comprimiendo el siguiente fichero: %s", filename)
                df = pd.read_csv (filename, parse_dates=['timestamp'])
                df = df.set_index ('timestamp')
                try:
                    df = df['LAST'].resample('5min').ohlc()
                except:
                    logging.error  ("Error comprimiendo %s. Esta vacio, creo uno igual", self.file_path_csv_)
                    with open(filename_comp, 'w') as f:
                        f.write('timestamp,open,high,low,close')
                else:
                    df.to_csv (filename_comp)
        logging.info  ("Salgo de mirar si hay que comprimir")


    def dbFileCheck (self):

        self.file_path_csv_ = self.dbGetFileName()
        self.file_path_csvPnL_ = self.dbGetFilePnLName()
        #logging.info  ("Creando o buscando fichero : %s", self.file_path_csv_)
        if not os.path.isfile(self.file_path_csv_):            
            try:   # Si el fichero no existe se crea
                df_temp = pd.DataFrame(columns = ['timestamp', 'BID', 'ASK', 'LAST', 'BID_SIZE', 'ASK_SIZE', 'LAST_SIZE'])
                df_temp.to_csv (self.file_path_csv_, index = False)
            except:
                logging.error  ("Problema creando fichero de market data: %s", self.file_path_csv_)
                return False
            
            try:   # Si no existe, tambien es probable que haya que comprimir
                self.dbCompressClosedFiles()
            except:
                logging.error  ("Problema comprimiendo ficheros")

        if not os.path.isfile(self.file_path_csvPnL_):  
            try:   # Si el fichero no existe se crea
                df_temp = pd.DataFrame(columns = ['timestamp', 'dailyPnL','realizedPnL','unrealizedPnL'])
                df_temp.to_csv (self.file_path_csvPnL_, index = False) # , index = False
            except:
                logging.error  ("Problema creando fichero de market data: %s", self.file_path_csvPnL_)
                return False
        #logging.info  ("Salgo de  fichero : %s", self.file_path_csv_)
        
        return True
        
    def dbUpdateAddPrices (self, data):
        
        keys_prices = ['BID', 'ASK', 'LAST', 'BID_SIZE', 'ASK_SIZE', 'LAST_SIZE']
        logging.debug ('Actulizamos con %s', data)
        
        if not self.dbFileCheck ():  # por si cambiamos de día. Pero hay que mejorar para que no lea todo el fichero si es houy
            return False

        incomplete = False

        try:
            lastone = self.df_.iloc[-1].to_dict()
        except:     # self.df_ es vacio. Se deja como incompleto para qie no escriba
            different = True
            for key in keys_prices: # Todos los valores que no traiga, los pongo a None
                if key not in data:
                    data[key] = None
                    incomplete = True
        else:
            different = False
            for key in keys_prices:  
                if key not in data:
                    if key in lastone: # Todos los valores que no tenga, los pillo de lastone, y si no None
                        data[key] = lastone[key]
                    else:
                        data[key] = None
                        incomplete = True
                if key in lastone and (lastone[key] != data[key]):
                    different = True
                elif key not in lastone and data[key] != None:
                    different = True

        newlineL = []
        newlineL.append (data)

        if different:
            self.dbUpdateInflux (data)
            dfDelta = pd.DataFrame.from_records(newlineL)
            dfDelta.set_index('timestamp', inplace=True)
            if incomplete:
                #self.df_ = dfDelta
                self.df_ = pd.concat([self.df_, dfDelta]) #, ignore_index=True
            else:
                self.df_ = pd.concat([self.df_, dfDelta]) #, ignore_index=True

                lastone = self.df_.iloc[-1:]
                lastone.to_csv(self.file_path_csv_, mode='a', header=False) #, index=False
                # Para asegurar que se graban bien (con todos los fields en orden), hay que crear un dataframe del ultimo del self.df

        if different:
            self.toPrint = True

    def dbUpdateAddPnL (self, data):
 
        keys_pnl = ['dailyPnL','realizedPnL','unrealizedPnL']
        logging.debug ('Actulizamos con %s', data)
        
        if not self.dbFileCheck ():  # por si cambiamos de día. Pero hay que mejorar para que no lea todo el fichero si es houy
            return False

        logging.debug ('[Pandas] - Pandas data: %s', data) 
        incomplete = False
        try:
            logging.debug ('[Pandas] - Escribir data0: %s', self.dfPnl_) 
            lastone = self.dfPnl_.iloc[-1].to_dict()
        except:     # self.dfPnl_ es vacio. Se deja como incompleto para qie no escriba
            differentPnL = True
            for key in keys_pnl: # Todos los valores que no traiga, los pongo a None
                if key not in data:
                    data[key] = None
                    incomplete = True
        else:
            differentPnL = False
            for key in keys_pnl:  
                if key not in data:
                    if key in lastone: # Todos los valores que no tenga, los pillo de lastone, y si no None
                        data[key] = lastone[key]
                    else:
                        data[key] = None
                        incomplete = True
                if key in lastone and (lastone[key] != data[key]):
                    differentPnL = True
                elif key not in lastone and data[key] != None:
                    differentPnL = True
            
        newlineL = []
        newlineL.append (data)

        if differentPnL:
            self.dbUpdateInflux (data)
            dfDelta = pd.DataFrame.from_records(newlineL)
            dfDelta.set_index('timestamp', inplace=True)
            if incomplete:
                self.dfPnl_ = pd.concat([self.dfPnl_, dfDelta])
            else:
                self.dfPnl_ = pd.concat([self.dfPnl_, dfDelta]) #, ignore_index=True

                logging.debug ('[Pandas] - Escribir data: %s', self.dfPnl_) 

                lastone = self.dfPnl_.iloc[-1:]
                logging.debug ('[Pandas] - Escribir data2: %s', lastone) 
                lastone.to_csv(self.file_path_csvPnL_, mode='a', header=False) # , index=False
                # Para asegurar que se graban bien (con todos los fields en orden), hay que crear un dataframe del ultimo del self.df

        if differentPnL:
            self.toPrintPnL = True

    def dbUpdateInflux (self, data):
        keys_prices = ['BID', 'ASK', 'LAST', 'BID_SIZE', 'ASK_SIZE', 'LAST_SIZE']
        keys_pnl = ['dailyPnL','realizedPnL','unrealizedPnL']

        bPrices = False
        bPnl = False
        
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
        fields_pnl = {}

        
        for key in keys_prices:
            if key in data:
                bPrices = True
                fields_prices[key] = data[key]

        for key in keys_pnl:
            if key in data:
                bPnl = True
                fields_pnl[key] = data[key]


        if bPrices:
            record = {
                "measurement": "precios", 
                "tags": tags,
                "fields": fields_prices,
                "time": time,
            }
            records.append(record)

        if bPnl:
            record = {
                "measurement": "pnl", 
                "tags": tags,
                "fields": fields_pnl,
                "time": time,
            }
            records.append(record)

        if bPnl or bPrices:
            self.influxIC_.write_data(records)

    # Estas son las nuevas:

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

        if bPnl or bPrices:
            self.influxIC_.write_data(records)
        


            
    
