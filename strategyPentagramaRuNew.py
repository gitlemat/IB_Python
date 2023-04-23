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
            line += '\n'
            lines.append(line)
        line = '%\n'
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
        # Potenciales estados de error:
        # Parent no ejecutada:
        #     - Sintomas:
        #         - Parent_id Null
        #         - Parent_id no existe segun IB
        #         - Parent order en estado inactivo ['Cancelled', 'PendingCancel', 'Inactive', 'ApiCancelled']
        #     - Accion:
        #         - Rehacer todo
        #     - Sintomas:
        #         - SL_id o TP_id Null
        #         - SL_id o TP_id no existe segun IB
        #         - SL_id o TP_id en estado erroneo orderChildValidExecStatus -> ['Filled', 'Submitted', 'Cancelled', 'PendingCancel', 'ApiCancelled']
        #     - Accion:
        #         - Rehacer las TP/SL (seguramente deshaciendo la que esta bien). Entiendo que se puede hacer usando parent_id
        #         - Quizá es mejor deshacer/cancel todo y rehacer
        # Parent ejecutada:
        #     - Sintoma:
        #         - SL_id o TP_id Null
        #         - SL_id o TP_id no existe segun IB
        #         - SL_id o TP_id en estado erroneo NO EN orderChildValidExecStatus -> ['Filled', 'Submitted', 'Cancelled', 'PendingCancel', 'ApiCancelled']
        #     - Accion:
        #         - Rehacer las TP/SL pero quizá haciendo un OCA nuevo. Follon necesario
        # En todos los casos:
        #     - Sintoma:
        #         - SL_id o TP_id Null
        #         - SL_id o TP_id no existe segun IB
        #     - Accion:
        #         - Rehacer las TP/SL dependiendo de si la parent está ejecutada o no
        #         - Si la parent está exec: OCA
        #         - Si la parent no está exec: igual hay que rehacer todo.


        
        if self.stratEnabled_ == False:
            return False

        bStrategyUpdated = False

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
                # Parent no ejecutada, y error en child
                if bSLOrderStatus in orderChildValidExecStatus:
                    bSLOrderError = True
                if bTPOrderStatus in orderChildValidExecStatus:
                    bTPOrderError = True
            # Si la parentOrder se ha ejecutado, las child tienen que estar en un estado valido. Si no error.
            else:
                if bSLOrderStatus not in orderChildValidExecStatus:
                    bSLOrderError = True
                if bTPOrderStatus not in orderChildValidExecStatus:
                    bTPOrderError = True
            # Si la OrderSL no existe: error siempre
            if zone['OrderIdSL'] == None or not bSLOrderExists:
                #logging.error ('Estrategia %s [PentagramaRu]. Error en SLOrder. OrderId %s', self.symbol_ ,zone['OrderIdSL'])
                bSLOrderError = True
            # Si la OrderTP no existe: error siempre
            if zone['OrderIdTP'] == None or not bTPOrderExists:
                #logging.error ('Estrategia %s [PentagramaRu]. Error en TPOrder. OrderId %s', self.symbol_ ,zone['OrderIdTP'])
                bTPOrderError = True                

            # Ahora vemos qué se hace por cada error
            #

            bRehacerTodo = False
            bGenerarOCA = False

            parentOrderId = zone['OrderId']

            # Si hemos detectado error en parent, borramos todas si no existen
            if bParentOrderError: # La parentId no está, y no está ejecutada. Borramos todas y rehacemos
                if (datetime.datetime.now() - self.timelasterror_) < Error_orders_timer_dt:
                    continue
                parentOrderId = None
                logging.error ('Estrategia %s [PentagramaRu]. Error en parentId', self.symbol_)
                if bParentOrderExists:
                    logging.error ('    Cancelamos la Parent OrderId %s', zone['OrderId'])
                    self.RTLocalData_.orderCancelByOrderId (zone['OrderId'])  
                if bSLOrderExists:
                    logging.error ('    Cancelamos la SLOrder OrderId %s', zone['OrderIdSL'])
                    self.RTLocalData_.orderCancelByOrderId (zone['OrderIdSL'])  
                if bSLOrderExists:
                    logging.error ('    Cancelamos la OrderIdTP OrderId %s', zone['OrderIdTP'])
                    self.RTLocalData_.orderCancelByOrderId (zone['OrderIdTP'])
                bRehacerTodo = True

            # Si hemos detectado error en alguna child, las borramos para recrear
            # TODOS MAL!!!!! No podemos recrear child con bracket orders si la parent está rellena
            # Si no esta exec: borramos todo y recrear
            # Si ya esta exec: Hacemos a mano la TP y SL
            elif bSLOrderError or bTPOrderError:
                if (datetime.datetime.now() - self.timelasterror_) < Error_orders_timer_dt:
                    continue
                logging.error ('Estrategia %s [PentagramaRu]. Error en childOrder', self.symbol_)
                if bSLOrderExists:
                    logging.error ('    Cancelamos la SLOrder OrderId %s', zone['OrderIdSL'])
                    self.RTLocalData_.orderCancelByOrderId (zone['OrderIdSL'])  
                if bSLOrderExists:
                    logging.error ('    Cancelamos la OrderIdTP OrderId %s', zone['OrderIdTP'])
                    self.RTLocalData_.orderCancelByOrderId (zone['OrderIdTP'])  
                if not zone['BracketOrderFilledState'] in ['ParentFilled', 'ParentFilled+F', 'ParentFilled+C']:
                    logging.error ('    Cancelamos la Parent OrderId %s', zone['OrderId'])
                    self.RTLocalData_.orderCancelByOrderId (zone['OrderId'])
                    bRehacerTodo = True
                else:
                    bGenerarOCA = True

            if bRehacerTodo or bGenerarOCA:
                self.timelasterror_ = datetime.datetime.now()
                new_zone = None
                if bRehacerTodo:
                    logging.error ('Estrategia %s [PentagramaRu]. Rehacemos todo', self.symbol_)
                    new_zone = self.strategyCreateBracketOrder (zone)
                elif bGenerarOCA:
                    logging.error ('Estrategia %s [PentagramaRu]. Rehacemos OCA para childs', self.symbol_)
                    new_zone = self.strategyCreateChildOca (zone)
                if new_zone != None:
                    self.zones_[iter] = new_zone   # Actualiza la zona
                    bStrategyUpdated = True
                    self.ordersUpdated_ = True

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

        bChanged = False

        if ordenObj != "":
            ret = self.strategyOrderIdUpdated (ordenObj)
            if ret:
                bChanged = True

        return bChanged
        

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
            orderIds = self.RTLocalData_.orderPlaceBracket (symbol, secType, action, qty, lmtPrice, takeProfitLimitPrice, stopLossPrice)
        except:
            logging.error('Error lanzando las barcket orders', exc_info = True)
            return None

        if orderIds == None:
            return None

        zone['OrderId'] = orderIds['parentOrderId']
        zone['OrderIdTP'] = orderIds['tpOrderId']
        zone['OrderIdSL'] = orderIds['slOrderId']

        return zone

    def strategyCreateChildOca (self, zone):

        symbol = self.symbol_
        contract = self.RTLocalData_.contractGetBySymbol(symbol)  
        secType = contract['contract'].secType
        action1 = 'BUY' if zone['B_S'] == 'B' else 'SELL'
        action2 = "SELL" if action1 == "BUY" else "BUY"
        qty = zone['Qty']
        takeProfitLimitPrice = zone['PrecioTP']
        stopLossPrice = zone['PrecioSL']

        try:
            logging.info ('Vamos a crear las ordenes SL/TP como OCA para %s', symbol)
            logging.info ('     Precio TP : %.3f', takeProfitLimitPrice)
            logging.info ('     Precio SL : %.3f', stopLossPrice)
            orderIds = self.RTLocalData_.orderPlaceOCA (symbol, secType, action1, action2, qty, takeProfitLimitPrice, stopLossPrice)
        except:
            logging.error('Error lanzando las OCA orders', exc_info=True)
            return None

        if orderIds == None:
            return None

        zone['OrderIdTP'] = orderIds['tpOrderId']
        zone['OrderIdSL'] = orderIds['slOrderId']

        return zone

    
