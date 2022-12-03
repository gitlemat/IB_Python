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
        self.df_ = None
        self.dfcomp_ = None
        self.symbol_ = symbol
        self.influxIC_ = influxIC
        self.dbInitFile ()
        self.toPrint = True
        self.toPrintPnL = True

    def dbInitFile (self):

        self.dbFileCheck()
        self.dbReadAllFiles()

    def dbReadAllFiles(self):
        path = 'market/'
        self.df_ = None
        self.dfcomp_ = pd.DataFrame(columns = ['timestamp','open','high','low','close'])
        logging.debug  ('Leer todos los ficheros')

        bSegundoLeido = False
        nReadLength = 0
        for i in sorted(os.listdir(path), reverse=True):
            filename = os.path.join(path,i)
            if os.path.isfile(filename) and i.startswith(self.symbol_+'_'):
                logging.debug  ('Analizamos %s', filename)
                if i.endswith ('_comp.csv'): # Los comprimidos los cargo todos
                    logging.debug  ('     .. es comprimido')
                    df_new = pd.read_csv (filename, parse_dates=['timestamp'], index_col=0)
                    self.dfcomp_ = pd.concat([self.dfcomp_, df_new])
                else:  # Los no comprimidos, solo hoy y el antyerior no vacio, por si estamos a mitad del dia
                    datefile = i[-10:-4]
                    todaystr = time.strftime("%y%m%d")
                    if datefile == todaystr or bSegundoLeido == False:
                        logging.debug  ('     .. es el no comprimido de hoy, o de undia anteriro para tener un minimo')
                        df_new = pd.read_csv (filename, parse_dates=['timestamp'])
                        self.df_ = pd.concat([self.df_, df_new])
                        nReadLength += len(df_new.index)
                        if nReadLength > 2000:
                            bSegundoLeido = True
        

        self.df_ = self.df_.sort_values(by=['timestamp'], ignore_index=True)
        self.dfcomp_ = self.dfcomp_.sort_values(by=['timestamp']) # El comp si tiene index

        logging.debug  ('--------------------')
        logging.debug  (self.symbol_)
        logging.debug  (self.df_)


    def dbGetDataframeToday(self):
        return self.df_

    def dbGetDataframeComp(self):
        return self.dfcomp_

    def dbGetFileName(self):
        return 'market/' + self.symbol_ + time.strftime("_%y%m%d") + '.csv'

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
            lastRecord = self.df_.iloc[-1]
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
            if os.path.isfile(filename) and filename != self.file_path_csv_ and i.startswith(self.symbol_+'_') and (not i.endswith ('_comp.csv')) and (not i_comp in dirlist): # Fichero de este simbolo que no esta comprimido
                #logging.info  ("Comprimiendo el siguiente fichero: %s", filename)
                df = pd.read_csv (filename, parse_dates=['timestamp'])
                df = df.set_index ('timestamp')
                try:
                    df = df['LAST'].resample('5min').ohlc()
                except:
                    logging.info  ("Error comprimiendo %s. Esta vacio, creo uno igual", self.file_path_csv_)
                    with open(filename_comp, 'w') as f:
                        f.write('timestamp,open,high,low,close')
                else:
                    df.to_csv (filename_comp)
        logging.info  ("Salgo de mirar si hay que comprimir")


    def dbFileCheck (self):

        self.file_path_csv_ = self.dbGetFileName()
        #logging.info  ("Creando o buscando fichero : %s", self.file_path_csv_)
        if not os.path.isfile(self.file_path_csv_):            
            try:   # Si el fichero no existe se crea
                df_temp = pd.DataFrame(columns = ['gConId', 'Symbol' ,'timestamp', 'BID', 'ASK', 'LAST', 'BID_SIZE', 'ASK_SIZE', 'LAST_SIZE','dailyPnL','realizedPnL','unrealizedPnL'])
                df_temp.to_csv (self.file_path_csv_, index = False)
            except:
                logging.error  ("Problema creando fichero de market data: %s", self.file_path_csv_)
                return False
            
            try:   # Si no existe, tambien es probable que haya que comprimir
                self.dbCompressClosedFiles()
            except:
                logging.error  ("Problema comprimiendo ficheros")
        #logging.info  ("Salgo de  fichero : %s", self.file_path_csv_)
        
        return True
        
    def dbUpdateAdd (self, data):
        
        keys = ['BID', 'ASK', 'LAST', 'BID_SIZE', 'ASK_SIZE', 'LAST_SIZE','dailyPnL','realizedPnL','unrealizedPnL']
        keys_prices = ['BID', 'ASK', 'LAST', 'BID_SIZE', 'ASK_SIZE', 'LAST_SIZE']
        keys_pnl = ['dailyPnL','realizedPnL','unrealizedPnL']
        logging.debug ('Actulizamos con %s', data)
        if data['Symbol'] != self.symbol_:
            return

        self.dbUpdateInflux (data)
        
        if not self.dbFileCheck ():  # por si cambiamos de día. Pero hay que mejorar para que no lea todo el fichero si es houy
            return False

        #print ("Pandas Data:", data)
        #logging.info ('[Pandas] - Pandas data: %s', data) 
        incomplete = False
        try:
            lastone = self.df_.iloc[-1].to_dict()
        except:     # self.df_ es vacio
            different = True
            differentPnL = True
            for key in keys:
                if key not in data:
                    data[key] = None
                    incomplete = True
        else:
            for key in keys:
                if key not in data:
                    if key in lastone:
                        data[key] = lastone[key]
                    else:
                        data[key] = None
                        incomplete = True

            different = False
            for key in keys_prices:
                if key in lastone and (lastone[key] != data[key]):
                    different = True
                elif data[key] != None:
                    different = True

            differentPnL = False
            for key in keys_pnl:
                if key in lastone and (lastone[key] != data[key]):
                    differentPnL = True
                elif data[key] != None:
                    differentPnL = True
            
        newlineL = []
        newlineL.append (data)

        if different or differentPnL:
            dfDelta = pd.DataFrame.from_records(newlineL)
            if incomplete:
                self.df_ = dfDelta
            else:
                dfDelta = pd.DataFrame.from_records(newlineL)
                self.df_ = pd.concat([self.df_, dfDelta], ignore_index=True)

                lastone = self.df_.iloc[-1:]
                lastone.to_csv(self.file_path_csv_, mode='a', index=False, header=False)
                # Para asegurar que se graban bien (con todos los fields en orden), hay que crear un dataframe del ultimo del self.df


        if different:
            self.toPrint = True

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
        tags = {'symbol': data['Symbol']}
        time = ['timestamp']
        
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


            
    
