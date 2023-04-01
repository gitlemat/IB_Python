import logging
import datetime
import pandasDB
from strategyClass import strategyBaseClass


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


orderChildErrorStatus = ['Inactive']
orderChildValidExecStatus = ['Filled', 'Submitted', 'Cancelled', 'PendingCancel', 'ApiCancelled']
orderInactiveStatus = ['Cancelled', 'PendingCancel', 'Inactive', 'ApiCancelled']
STRAT_File = 'strategies/RU_Pentagrama.conf'


def strategyReadFile (RTlocalData):
    with open(STRAT_File) as f:
        lines = f.readlines()

    lstrategyList = []        
    
    logging.info ('Cargando Estrategias Pentagrama Ruben')
    
    lineSymbol = None
    lineStratEnabled = False
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
            zone = {}
            try:
                zone['B_S'] = fields[0].strip()
                zone['Price'] = float(fields[1].strip())
                zone['Qty'] = int(fields[2].strip())
                zone['PrecioSL'] = float(fields[3].strip())
                zone['PrecioTP'] = float(fields[4].strip())
            except:
                bError = True
            if fields[5].strip() == ''  or fields[5].strip() == 'None':
                zone['OrderId'] = None
            else:
                zone['OrderId'] = int (fields[5].strip())
            if fields[6].strip() == ''  or fields[6].strip() == 'None':
                zone['OrderPermId'] = None
            else:
                zone['OrderPermId'] = int (fields[6].strip())
            if fields[7].strip() == ''  or fields[7].strip() == 'None':
                zone['OrderIdSL'] = None
            else:
                zone['OrderIdSL'] = int (fields[7].strip())
            if fields[8].strip() == ''  or fields[8].strip() == 'None':
                zone['OrderPermIdSL'] = None
            else:
                zone['OrderPermIdSL'] = int (fields[8].strip())
            if fields[9].strip() == ''  or fields[9].strip() == 'None':
                zone['OrderIdTP'] = None
            else:
                zone['OrderIdTP'] = int (fields[9].strip())
            if fields[10].strip() == ''  or fields[10].strip() == 'None':
                zone['OrderPermIdTP'] = None
            else:
                zone['OrderPermIdTP'] = int (fields[10].strip())
            if fields[11].strip() == 'ParentFilled' or fields[11].strip() == 'ParentFilled+F' or fields[11].strip() == 'ParentFilled+C' :
                zone['BracketOrderFilledState'] = fields[11].strip()
            else:
                zone['BracketOrderFilledState'] = None
            
            logging.info ('############## %s', zone)
            zones.append(zone)

        elif fields[0].strip() == '%':
            zones = sorted(zones, key=lambda d: d['Price'], reverse=True)
            ahora = datetime.datetime.now() - datetime.timedelta(seconds=15)
            datafields = {'stratEnabled': lineStratEnabled, 'currentPos': lineCurrentPos, 'zones': zones, 'ordersUpdated': True}
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
            if fields[2].strip() == '':
                lineCurrentPos = None   
            else:
                lineCurrentPos = int (fields[2].strip())

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
        line += ' \n' if strategyItem['classObject'].currentPos_ == None else str(int(strategyItem['classObject'].currentPos_)) + '\n'
        lines.append(line)
        for zone in strategyItem['classObject'].zones_:
            line = zone['B_S'] + ','
            line += str(zone['Price']) + ','
            line += str(zone['Qty']) + ','
            line += str(zone['PrecioSL']) + ','
            line += str(zone['PrecioTP']) + ','
            line += str(zone['OrderId']) + ','
            line += str(zone['OrderPermId']) + ','
            line += str(zone['OrderIdSL']) + ','
            line += str(zone['OrderPermIdSL']) + ','
            line += str(zone['OrderIdTP']) + ','
            line += str(zone['OrderPermIdTP']) + ','
            line += str(zone['BracketOrderFilledState'])
            lines.append(line)
        line = '%'
        lines.append(line)
    with open(STRAT_File, 'w') as f:
        for line in lines:
            f.writelines(line)

class strategyPentagramaRu(strategyBaseClass):

    def __init__(self, RTlocalData, symbol, data):
        self.RTLocalData_ = RTlocalData

        self.symbol_ = symbol
        self.stratEnabled_ = data['stratEnabled']
        self.currentPos_ = data['currentPos']
        self.zones_ = data['zones']
        self.ordersUpdated_ = data['ordersUpdated']
        self.pandas_ = pandasDB.dbPandasStrategy (self.symbol_, 'PentagramaRu', self.RTLocalData_.influxIC_)  
        self.timelasterror_ = datetime.datetime.now()
    
    def strategyGetIfOrderId(self, orderId):
        for zone in self.zones_:
            if zone['OrderId'] == orderId or zone['OrderIdSL'] == orderId or zone['OrderIdTP'] == orderId:
                return True
        return False

    def strategyEnableDisable (self, state):
        self.stratEnabled_ = state
        return True # La strategies new tiene que actualizar fichero!!!

    def strategyCheckEnabled (self):
        # Devolver si está habilidata o no 
        return self.stratEnabled_

    def strategyLoopCheck (self): 

        if self.stratEnabled_ == False:
            return False
        for iter in range(len(self.zones_)):
            zone = self.zones_[iter]
            bParentOrderError = False
            bParentOrderExists = self.RTLocalData_.orderCheckIfExistsByOrderId(zone['OrderId'])
            bParentOrderStatus = self.RTLocalData_.orderGetStatusbyOrderId (zone['OrderId'])
            bSLOrderError = False
            bSLOrderExists = self.RTLocalData_.orderCheckIfExistsByOrderId(zone['OrderIdSL'])
            bSLOrderStatus = self.RTLocalData_.orderGetStatusbyOrderId (zone['OrderIdSL'])
            bTPOrderError = False
            bTPOrderExists = self.RTLocalData_.orderCheckIfExistsByOrderId(zone['OrderIdTP'])
            bTPOrderStatus = self.RTLocalData_.orderGetStatusbyOrderId (zone['OrderIdTP'])
            # Si no tengo constancia de que se halla comprado la parent, si no existe es error
            if not zone['BracketOrderFilledState'] in ['ParentFilled', 'ParentFilled+F', 'ParentFilled+C']:
                if zone['OrderId'] == None or not bParentOrderExists or bParentOrderStatus in orderInactiveStatus:
                    bParentOrderError = True
            # Si la parentOrder se ha ejecutado, las child tienen que estar en un estado valido. Si no error.
            else:
                if bSLOrderStatus not in orderChildValidExecStatus:
                    bSLOrderError = True
                if bTPOrderStatus not in orderChildValidExecStatus:
                    bTPOrderError = True
            # Si la OrderSL no existe: error siempre
            if zone['OrderIdSL'] == None or not bSLOrderExists:
                logging.error ('Estrategia %s [PentagramaRu]. Error en SLOrder. OrderId %s', self.symbol_ ,zone['OrderIdSL'])
                bSLOrderError = True
            # Si la OrderTP no existe: error siempre
            if zone['OrderIdTP'] == None or not bTPOrderExists:
                logging.error ('Estrategia %s [PentagramaRu]. Error en TPOrder. OrderId %s', self.symbol_ ,zone['OrderIdTP'])
                bTPOrderError = True                

            # Ahora vemos qué se hace por cada error
            #

            parentOrderId = zone['OrderId']

            # Si hemos detectado error en parent, borramos todas si no existen
            if bParentOrderError: # La parentId no está, y no está ejecutada. Borramos todas y rehacemos
                if (datetime.datetime.now() - self.timelasterror_) < Error_orders_timer_dt:
                    continue
                parentOrderId = None
                if bParentOrderExists:
                    logging.error ('Estrategia %s [PentagramaRu]. Error en parentId. Cancelamos la Parent OrderId %s', self.symbol_ ,zone['OrderId'])
                    self.RTLocalData_.orderCancelByOrderId (zone['OrderId'])  
                if bSLOrderExists:
                    logging.error ('Estrategia %s [PentagramaRu]. Error en parentId. Cancelamos la SLOrder OrderId %s', self.symbol_ ,zone['OrderIdSL'])
                    self.RTLocalData_.orderCancelByOrderId (zone['OrderIdSL'])  
                if bSLOrderExists:
                    logging.error ('Estrategia %s [PentagramaRu]. Error en parentId. Cancelamos la OrderIdTP OrderId %s', self.symbol_ ,zone['OrderIdTP'])
                    self.RTLocalData_.orderCancelByOrderId (zone['OrderIdTP'])  

            # Si hemos detectado error en alguna child, las borramos para recrear
            # TODOS MAL!!!!! No podemos recrear child con bracket orders si la parent está rellena
            # Si no esta exec: borramos todo y recrear
            # Si ya esta exec: Hacemos a mano la TP y SL
            if bSLOrderError or bTPOrderError:
                if bSLOrderExists:
                    logging.error ('Estrategia %s [PentagramaRu]. Error en childOrder. Cancelamos la SLOrder OrderId %s', self.symbol_ ,zone['OrderIdSL'])
                    self.RTLocalData_.orderCancelByOrderId (zone['OrderIdSL'])  
                if bSLOrderExists:
                    logging.error ('Estrategia %s [PentagramaRu]. Error en childOrder. Cancelamos la OrderIdTP OrderId %s', self.symbol_ ,zone['OrderIdTP'])
                    self.RTLocalData_.orderCancelByOrderId (zone['OrderIdTP'])  

            if bParentOrderError or bSLOrderError or bTPOrderError:   # está mal. Las condiciones hay que ponerlas bien
                if (datetime.datetime.now() - self.timelasterror_) < Error_orders_timer_dt:
                    continue

                new_zone = self.strategyCreateBracketOrder (zone)
                if new_zone != None:
                    self.zones_[iter] = new_zone   # Actualiza la zona
                    bStrategyUpdated = True
                    self.ordersUpdated_ = True
                else:
                    self.timelasterror_ = datetime.datetime.now()
        
        return bStrategyUpdated

    def strategyReloadFromFile(self):
        with open(STRAT_File) as f:
            lines = f.readlines()
        
        logging.info ('Leyendo Estrategia %s [PentagramaRu] de fichero', self.symbol_)
        
        lineSymbol = None
        lineStratEnabled = False
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
                zone = {}
                try:
                    zone['B_S'] = fields[0].strip()
                    zone['Price'] = float(fields[1].strip())
                    zone['Qty'] = int(fields[2].strip())
                    zone['PrecioSL'] = float(fields[3].strip())
                    zone['PrecioTP'] = float(fields[4].strip())
                except:
                    bError = True
                if fields[5].strip() == ''  or fields[5].strip() == 'None':
                    zone['OrderId'] = None
                else:
                    zone['OrderId'] = int (fields[5].strip())
                if fields[6].strip() == ''  or fields[6].strip() == 'None':
                    zone['OrderPermId'] = None
                else:
                    zone['OrderPermId'] = int (fields[6].strip())
                if fields[7].strip() == ''  or fields[7].strip() == 'None':
                    zone['OrderIdSL'] = None
                else:
                    zone['OrderIdSL'] = int (fields[7].strip())
                if fields[8].strip() == ''  or fields[8].strip() == 'None':
                    zone['OrderPermIdSL'] = None
                else:
                    zone['OrderPermIdSL'] = int (fields[8].strip())
                if fields[9].strip() == ''  or fields[9].strip() == 'None':
                    zone['OrderIdTP'] = None
                else:
                    zone['OrderIdTP'] = int (fields[9].strip())
                if fields[10].strip() == ''  or fields[10].strip() == 'None':
                    zone['OrderPermIdTP'] = None
                else:
                    zone['OrderPermIdTP'] = int (fields[10].strip())
                
                zones.append(zone)
    
            elif fields[0].strip() == '%':
                if lineSymbol == self.symbol_:
                    bFound = True
                    if not bError:
                        zones = sorted(zones, key=lambda d: d['Price'], reverse=True)
                        self.stratEnabled_ = lineStratEnabled
                        self.currentPos_ = lineCurrentPos
                        self.zones_ = zones
                        self.ordersUpdated_ = True
                        logging.info ('Estrategia %s [PentagramaRu] recargada de fichero', self.symbol_)
                    else:
                        logging.error ('Error leyendo los valores de la estrategia %s [PentagramaRu]', self.symbol_)
                        return False
                    break # No hace falta seguir
                zones = []
            else:
                lineSymbol = fields[0].strip()
                if fields[1].strip() == '' or fields[1].strip() == '0' or fields[1].strip() == 'False' :
                    lineStratEnabled = False
                else:
                    lineStratEnabled = True
                if fields[2].strip() == '':
                    lineCurrentPos = None   
                else:
                    lineCurrentPos = int (fields[2].strip())

        if bFound == False:
            logging.error ('No he encontrado la linea en el fichero que actualiza esta estrategia %s', self.symbol_)
            return False


    def strategyOrderUpdated (self, data):

        if self.stratEnabled_ == False:
            return False

        ordenObj = data['orderObj']
        self.strategyOrderIdUpdated (ordenObj)

    def strategyOrderIdUpdated (self, ordenObj):
        bChanged = False
        symbol = self.symbol_
        for zone in self.zones_:
            if zone['OrderPermId'] == None and zone['OrderId'] == ordenObj.orderId:
                logging.info ('Orden actualizada en estrategia %s. Nueva OrderPermId: %s', symbol, ordenObj.permId)
                zone['OrderPermId'] = ordenObj.permId
                bChanged = True
            elif zone['OrderPermIdSL'] == None and zone['OrderIdSL'] == ordenObj.orderId:
                logging.info ('Orden actualizada en estrategia %s. Nueva OrderPermIdSL: %s', symbol, ordenObj.permId)
                zone['OrderPermIdSL'] = ordenObj.permId
                bChanged = True
            elif zone['OrderPermIdTP'] == None and zone['OrderIdTP'] == ordenObj.orderId:
                logging.info ('Orden actualizada en estrategia %s. Nueva OrderPermIdTP: %s', symbol, ordenObj.permId)
                zone['OrderPermIdTP'] = ordenObj.permId
                bChanged = True
            elif zone['OrderPermId'] == ordenObj.permId and zone['OrderId'] != ordenObj.orderId:  # Esto es por si el orderId cambia (el permId no puede cambiar)
                logging.info ('Orden actualizada en estrategia (o inicializamos) %s. Nueva OrderId: %s', symbol, ordenObj.orderId)
                zone['OrderId'] = ordenObj.orderId
                bChanged = True
            elif zone['OrderPermIdSL'] == ordenObj.permId and zone['OrderIdSL'] != ordenObj.orderId:  # Esto es por si el orderId cambia (el permId no puede cambiar)
                logging.info ('Orden actualizada en estrategia (o inicializamos) %s. Nueva OrderIdSL: %s', symbol, ordenObj.orderId)
                zone['OrderIdSL'] = ordenObj.orderId
                bChanged = True
            elif zone['OrderPermIdTP'] == ordenObj.permId and zone['OrderIdTP'] != ordenObj.orderId:  # Esto es por si el orderId cambia (el permId no puede cambiar)
                logging.info ('Orden actualizada en estrategia (o inicializamos) %s. Nueva OrderIdTP: %s', symbol, ordenObj.orderId)
                zone['OrderIdTP'] = ordenObj.orderId
                bChanged = True
        
        if bChanged:
            self.ordersUpdated_ = True

        return bChanged

    def strategyCreateBracketOrder (self, zone):

        symbol = self.symbol_
        contract = self.RTLocalData_.contractGetBySymbol(symbol)  
        secType = contract['contract'].secType
        action = 'BUY' if zone['B_S'] == 'B' else 'SELL'
        qty = zone['Qty']
        lmtPrice = zone['Price']
        takeProfitLimitPrice = zone['PrecioTP']
        stopLossPrice = zone['PrecioSL']

        try:
            logging.info ('Vamos a crear la triada de ordenes bracket para %s', symbol)
            logging.info ('     Precio LMT: %.3f', lmtPrice)
            logging.info ('     Precio TP : %.3f', takeProfitLimitPrice)
            logging.info ('     Precio SL : %.3f', stopLossPrice)
            orderIds = self.RTLocalData_.orderPlaceBracket (self, symbol, secType, action, qty, lmtPrice, takeProfitLimitPrice, stopLossPrice)
        except:
            logging.error('Error lanzando las barcket orders para %s', symbol)
            return None

        if orderIds == None:
            return None

        zone['OrderId'] = orderIds['parentOrderId']
        zone['OrderIdTP'] = orderIds['tpOrderId']
        zone['OrderIdSL'] = orderIds['slOrderId']

        return zone
