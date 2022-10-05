import pandas as pd
import matplotlib.pyplot as plt
import os.path
import time


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
        self.symbol_ = symbol
        self.dbInitFile ()

    def dbInitFile (self):

        self.dbFileCheck()
        self.dbReadAllFiles()

    def dbReadAllFiles(self):
        path = 'market/'
        for i in os.listdir(path):
            filename = os.path.join(path,i)
            if os.path.isfile(filename) and i.startswith(self.symbol_+'_'):
                df_new = pd.read_csv (filename, parse_dates=['timestamp'])
                self.df_ = pd.concat([self.df_, df_new], ignore_index=True)
        self.df_ = self.df_.sort_values(by=['timestamp'], ignore_index=True)
        print ('--------------------')
        print (self.symbol_)
        print (self.df_)

    def dbGetDataframe(self):
        return self.df_


    def dbGetFileName(self):
        return 'market/' + self.symbol_ + time.strftime("_%y%m%d") + '.csv'

    def dbFileCheck (self):
        self.file_path_csv_ = self.dbGetFileName()
        if not os.path.isfile(self.file_path_csv_):
            self.df_ = pd.DataFrame(columns = ['gConId', 'Symbol' ,'timestamp', 'BID', 'ASK', 'LAST', 'BID_SIZE', 'ASK_SIZE', 'LAST_SIZE'])
            try:
                self.df_.to_csv (self.file_path_csv_, index = False)
            except:
                return False
        
        return True
        
    def dbUpdateAdd (self, data):
        if data['Symbol'] != self.symbol_:
            return
        newlineL = []
        newlineL.append (data)
        if not self.dbFileCheck ():  # por si cambiamos de día. Pero hay que mejorar para que no lea todo el fichero si es houy
            return False

        print ("Pandas Data:", data)
        try:
            lastone = self.df_.iloc[-1].to_dict()
            print ("Pandas Last:", lastone)
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

            # Para asegurar que se graban bien (con todos los fields en orden), hay que crear un dataframe del ultimo del self.df
            lastone = self.df_.iloc[-1:]
            lastone.to_csv(self.file_path_csv_, mode='a', index=False, header=False)
    
