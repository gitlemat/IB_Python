import logging
import datetime
import pandasDB
import strategyOrderBlock
from strategyClass2 import strategyBaseClass


logger = logging.getLogger(__name__)
Error_orders_timer_dt = datetime.timedelta(seconds=90)

#  ------------ 2
#
#
#  ------------ 1
#
#
#  ------------ 0
# 
#
# strategyItem['symbol']
# strategyItem['stratEnabled']
# strategyItem['currentPos']
# strategyItem['zones'][{'B_S','Price', 'Qty', 'PrecioSL', 'PrecioTP', 'OrderId', 'OrderPermId', 'OrderIdSL', 'OrderPermIdSL', 'OrderIdTP', 'OrderPermIdTP', 'BracketOrderFilledState'}]
# strategyItem['zonesNOP'][{'B_S','Price', 'Qty', 'PrecioSL', 'PrecioTP', 'OrderId', 'OrderPermId', 'OrderIdSL', 'OrderPermIdSL', 'OrderIdTP', 'OrderPermIdTP', 'BracketOrderFilledState'}]
# strategyItem['timelasterror']
# strategyItem['ordersUpdated']
#
# Cada zona tiene un BracketOrderFilledState que puede ser:
# - ParentFilled: La parent se ha ejecutado, el resto tienen que estar en submitted/cancel/Filled
# - ParentFilled+F: La parent se ha ejecutado, y una child ya ha ejecutado
# - ParentFilled+C: La parent se ha ejecutado, y una child cancelada (la otra debería estar rellenada, pero igual está por llegar)



STRAT_File = 'strategies/RU_Pentagrama.conf'


def strategyReadFile (RTlocalData):
    with open(STRAT_File) as f:
        lines = f.readlines()

    lstrategyList = []        
    
    logging.info ('Cargando Estrategias Pentagrama Ruben')
    
    lineSymbol = None
    lineStratEnabled = False
    lineStratCerrar = False
    lineCurrentPos = None 
    zones = []


    for line in lines[1:]: # La primera linea es el header
        bError = False
        if line[0] == '#':
            continue
        if line == '':
            continue
        logging.info ('############## %s', line)

        fields = line.split(',')
        if fields[0].strip() in ['B', 'S']:
            zone = strategyOrderBlock.bracketOrderParseFromFile(fields)
            if zone is not None:
                zones.append(zone)
            else:
                bError = True
        elif fields[0].strip() == '%':
            zones = sorted(zones, key=lambda d: d['Price'], reverse=True)
            ahora = datetime.datetime.now() - datetime.timedelta(seconds=15)
            datafields = {'stratEnabled': lineStratEnabled, 'cerrarPos': lineStratCerrar, 'currentPos': lineCurrentPos, 'zones': zones, 'ordersUpdated': True}
            if not bError:
                classObject = strategyPentagramaRu (RTlocalData, lineSymbol, datafields)
                lineFields = {'symbol': lineSymbol, 'type': 'PentagramaRu', 'classObject': classObject}
                lstrategyList.append(lineFields)
            zones = []
        else:
            lineSymbol = fields[0].strip()
            if fields[1].strip() == '' or fields[1].strip() == '0' or fields[1].strip() == 'False' :
                lineStratEnabled = False
            else:
                lineStratEnabled = True
            if fields[2].strip() == '' or fields[2].strip() == '0' or fields[2].strip() == 'False' :
                lineStratCerrar = False
            else:
                lineStratCerrar = True
            if fields[3].strip() == '':
                lineCurrentPos = None   
            else:
                lineCurrentPos = int (fields[3].strip())

    logging.info ('Estrategias Pentagrama cargadas')

    return lstrategyList

def strategyWriteFile (strategies):  
    lines = []
    header = '# Symbol        , En, CurrPos, \n'
    lines.append(header)
    header = '# B/S,Price,qty,PrecioSL,PrecioTP,OrdId,OrdPermId,OrdIdSL,OrdPermIdSL,OrdIdTP,OrdPermIdTP,\n'
    lines.append(header)
    lines.append(header)
    lines.append(header)
    for strategyItem in strategies:
        line = str(strategyItem['symbol']) + ','
        line += 'True,' if strategyItem['classObject'].stratEnabled_ == True else 'False,'
        line += 'True,' if strategyItem['classObject'].cerrarPos_ == True else 'False,'
        line += ' \n' if strategyItem['classObject'].currentPos_ == None else str(int(strategyItem['classObject'].currentPos_)) + '\n'
        lines.append(line)
        for zone in strategyItem['classObject'].zones_:
            line = strategyOrderBlock.bracketOrderParseFromFile(zone['orderBlock'])
            lines.append(line)
        line = '%\n'
        lines.append(line)
    with open(STRAT_File, 'w') as f:
        for line in lines:
            f.writelines(line)

class strategyPentagramaRu(strategyBaseClass):

    def __init__(self, RTlocalData, symbol, data):
        super().__init__(RTlocalData, symbol, data)

        # De la super_class:
        #   self.RTLocalData_ = RTlocalData
        #   self.symbol_ = symbol
        #   self.stratEnabled_ = data['stratEnabled']
        #   self.cerrarPos_ = data['cerrarPos']
        #   self.currentPos_ = data['currentPos']
        #   self.ordersUpdated_ = data['ordersUpdated']
        #   self.pandas_ = pandasDB.dbPandasStrategy (self.symbol_, 'PentagramaRu', self.RTLocalData_.influxIC_)  
        #   self.orderBlocks_ = []
        #   self.timelasterror_ = datetime.datetime.now()

        self.straType_ = 'PentagramaRu'
        self.zones_ = [] # En realidad es innecesario. Podemos considerar zone=orderBlock

        # Da la casualidad que cada zona corresponde a un BracketOrder. Es innecesario mantener zones_, pero por si mas adelante hace falta
        for zoneItem in data['zones']:
            orderBlock = strategyOrderBlock.bracketOrderClass(zoneItem, self.straType_, self.RTLocalData_)
            zone = {'orderBlock': orderBlock}
            self.zones_.append(zone)
            # En todas las strats tiene que haber una lista con todos los orderBlocks
            self.orderBlocks_.append(orderBlock)

    def strategyLoopCheck (self): 
        # Nada fuera de lo normal. Hacemos solo lo standard de la clase base
        super().strategyLoopCheck()


    def strategyOrderUpdated (self, data):

        new_pos = self.strategyCalcularPosiciones()

        zero_crossing = False

        if self.currentPos_ != new_pos:
            if new_pos == 0 or (new_pos * self.currentPos_ < 0):
                zero_crossing = True
            if self.cerrarPos_ and zero_crossing:
                logging.info ('')
                logging.info ('[Estrategia PentagramaRu (%s)] Hemos pasado por Cero y estrategio disabled por parametro: %s', self.symbol_, str(self.cerrarPos_))
                self.stratEnabled_ = False
            self.currentPos_ = new_pos
            bChanged = True

        return bChanged
        

    def strategyCalcularPosiciones (self):
        pos = 0
        for zone in self.zones_:
            # Cada zone solo tiene 1 orderBlock:
            orderBlock = zone['orderBlock']
            pos += orderBlock.orderBlockPosiciones()
        return pos
   

    def strategyReloadFromFile(self):
        with open(STRAT_File) as f:
            lines = f.readlines()
        
        logging.info ('[Estrategia PentagramaRu (%s)] Leyendo Estrategia de fichero', self.symbol_)
        
        lineSymbol = None
        lineStratEnabled = False
        lineStratCerrar = False
        lineCurrentPos = None 
        zones = []


        for line in lines[1:]: # La primera linea es el header
            bError = False
            bFound = False
            if line[0] == '#':
                continue
            if line == '':
                continue
    
            fields = line.split(',')
            if fields[0].strip() in ['B', 'S']:
                zone = strategyOrderBlock.bracketOrderParseFromFile(fields)
                if zone is not None:
                    zones.append(zone)
                else:
                    bError = True
    
            elif fields[0].strip() == '%':
                if lineSymbol == self.symbol_:
                    bFound = True
                    if not bError:
                        zones = sorted(zones, key=lambda d: d['Price'], reverse=True)
                        self.stratEnabled_ = lineStratEnabled
                        self.cerrarPos_ = lineStratCerrar
                        self.currentPos_ = lineCurrentPos
                        self.zones_ = zones
                        self.ordersUpdated_ = True
                        logging.info ('[Estrategia PentagramaRu (%s)] Recargada de fichero', self.symbol_)
                    else:
                        logging.error ('[Estrategia PentagramaRu (%s)] Error leyendo los valores de la estrategia', self.symbol_)
                        return False
                    break # No hace falta seguir
                zones = []
            else:
                lineSymbol = fields[0].strip()
                if fields[1].strip() == '' or fields[1].strip() == '0' or fields[1].strip() == 'False' :
                    lineStratEnabled = False
                else:
                    lineStratEnabled = True
                if fields[2].strip() == '' or fields[2].strip() == '0' or fields[2].strip() == 'False' :
                    lineStratCerrar = False
                else:
                    lineStratCerrar = True
                if fields[3].strip() == '':
                    lineCurrentPos = None   
                else:
                    lineCurrentPos = int (fields[3].strip())

        if bFound == False:
            logging.error ('[Estrategia PentagramaRu (%s)] No he encontrado la linea en el fichero que actualiza esta estrategia', self.symbol_)
            return False

    

    