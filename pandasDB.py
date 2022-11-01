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

    def __init__(self, symbol):
        self.file_path_csv_ = None
        self.df_ = None
        self.dfcomp_ = None
        self.symbol_ = symbol
        self.dbInitFile ()
        self.toPrint = True

    def dbInitFile (self):

        self.dbFileCheck()
        self.dbReadAllFiles()

    def dbReadAllFiles(self):
        path = 'market/'
        self.df_ = None
        self.dfcomp_ = None
        logging.info  ('Leer todos los ficheros')
        for i in sorted(os.listdir(path), reverse=True):
            filename = os.path.join(path,i)
            if os.path.isfile(filename) and i.startswith(self.symbol_+'_'):
                logging.debug  ('Analizamos %s', filename)
                if i.endswith ('_comp.csv'): # Los comprimidos los cargo todos
                    logging.debug  ('     .. es comprimido')
                    df_new = pd.read_csv (filename, parse_dates=['timestamp'], index_col=0)
                    self.dfcomp_ = pd.concat([self.dfcomp_, df_new])
                else:  # Los no comprimidos, solo hoy, por si estamos a mitad del dia
                    datefile = i[-10:-4]
                    todaystr = time.strftime("%y%m%d")
                    if datefile == todaystr:
                        logging.debug  ('     .. es el no comprimido de hoy')
                        self.df_ = pd.read_csv (filename, parse_dates=['timestamp'])
        self.df_ = self.df_.sort_values(by=['timestamp'], ignore_index=True)
        self.dfcomp_ = self.dfcomp_.sort_values(by=['timestamp']) # El comp si tiene index

        logging.debug  ('--------------------')
        logging.debug  (self.symbol_)
        logging.debug  (self.df_)

    def dbGetPrevDay(self):
        hoy = datetime.date.today()


    def dbGetDataframeToday(self):
        return self.df_

    def dbGetDataframeComp(self):
        return self.dfcomp_

    def dbGetFileName(self):
        return 'market/' + self.symbol_ + time.strftime("_%y%m%d") + '.csv'

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
                self.df_ = pd.DataFrame(columns = ['gConId', 'Symbol' ,'timestamp', 'BID', 'ASK', 'LAST', 'BID_SIZE', 'ASK_SIZE', 'LAST_SIZE'])
                self.df_.to_csv (self.file_path_csv_, index = False)
            except:
                logging.error  ("Problema creando fichero de market data: %s", self.file_path_csv_)
                return False
            self.dbCompressClosedFiles()
            try:   # Si no existe, tambien es probable que haya que comprimir
                pass
            except:
                logging.error  ("Problema comprimiendo ficheros")
        #logging.info  ("Salgo de  fichero : %s", self.file_path_csv_)
        
        return True
        
    def dbUpdateAdd (self, data):
        if data['Symbol'] != self.symbol_:
            return
        newlineL = []
        newlineL.append (data)
        if not self.dbFileCheck ():  # por si cambiamos de día. Pero hay que mejorar para que no lea todo el fichero si es houy
            return False

        #print ("Pandas Data:", data)
        #logging.info ('[Pandas] - Pandas data: %s', data) 
        try:
            lastone = self.df_.iloc[-1].to_dict()
            #print ("Pandas Last:", lastone)
            #logging.info ('[Pandas] - Pandas last: %s', lastone)
        except:
            different = True
        else:
            different = lastone['ASK'] != data['ASK']
            different += lastone['BID'] != data['BID']
            different += lastone['LAST'] != data['LAST']
            different += lastone['ASK_SIZE'] != data['ASK_SIZE']
            different += lastone['BID_SIZE'] != data['BID_SIZE']
            different += lastone['LAST_SIZE'] != data['LAST_SIZE']

        print ("Pandas different:", different)

        if different:
            dfDelta = pd.DataFrame.from_records(newlineL)
            self.df_ = pd.concat([self.df_, dfDelta], ignore_index=True)
            self.toPrint = True

            # Para asegurar que se graban bien (con todos los fields en orden), hay que crear un dataframe del ultimo del self.df
            lastone = self.df_.iloc[-1:]
            lastone.to_csv(self.file_path_csv_, mode='a', index=False, header=False)
    
