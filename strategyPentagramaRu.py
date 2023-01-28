import logging
import datetime


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
# strategyItem['zones'][{'B_S','Price', 'Qty', 'PrecioSL', 'PrecioTP', 'OrderId', 'OrderPermId', 'OrderIdSL', 'OrderPermIdSL', 'OrderIdTP', 'OrderPermIdTP'}]
# strategyItem['zonesNOP'][{'B_S','Price', 'Qty', 'PrecioSL', 'PrecioTP', 'OrderId', 'OrderPermId', 'OrderIdSL', 'OrderPermIdSL', 'OrderIdTP', 'OrderPermIdTP'}]
# strategyItem['timelasterror']
# strategyItem['ordersUpdated']


orderInactiveStatus = ['Cancelled', 'Filled', 'PendingCancel', 'Inactive', 'ApiCancelled']

class strategyPentagramaRu():

    def __init__(self, RTlocalData):
        self.RTLocalData_ = RTlocalData
        self.strategyList_ = []
        self.strategyPentagramaRuReadFile()
        try:
            
            logging.info('Leyendo la estrategia Pentagrama Ruben:')
            logging.info('     %s', self.strategyList_)
        except:
            logging.error ('Error al cargar el fichero strategies/Ru_Pentagrama.conf')
            # Print un error al cargar 

    def strategyPentagramaRuGetAll(self):
        return self.strategyList_

    def strategyPentagramaRuGetStrategyBySymbol(self, symbol):
        for estrategia in self.strategyList_:
            lsymbol = estrategia['symbol']
            if lsymbol == symbol:
                return estrategia
        return None
    
    def strategyPentagramaRuGetStrategyByOrderId(self, orderId):
        for currentSymbolStrategy in self.strategyList_:
            lsymbol = currentSymbolStrategy['symbol']
            for zone in currentSymbolStrategy['zones']:
                if zone['OrderId'] == orderId or zone['OrderIdSL'] == orderId or zone['OrderIdTP'] == orderId:
                    return {'strategy':'PentagramaRu', 'symbol':lsymbol}
        return None

    def strategyPentagramaRuEnableDisable (self, symbol, state):
        for symbolStrategy in self.strategyList_:
            if symbolStrategy['symbol'] == symbol:
                symbolStrategy['stratEnabled'] = state
                self.strategyPentagramaRuUpdate (symbolStrategy)
                break

    def strategyPentagramaRuCheckEnabled (self, symbol):
        # Devolver si está habilidata o no 
        enabled = False
        for symbolStrategy in self.strategyList_:
            if symbolStrategy['symbol'] == symbol:
                enabled = symbolStrategy['stratEnabled']
                break

        return enabled

    def strategyPentagramaRuLoopCheck (self): 
        
        for currentSymbolStrategy in self.strategyList_:
            bStrategyUpdated = False
            if currentSymbolStrategy['stratEnabled'] == False:
                continue
            for iter in range(len(currentSymbolStrategy['zones'])):
                zone = currentSymbolStrategy['zones'][iter]
                bOrderError = False
                bOrderExists = self.RTLocalData_.orderCheckIfExistsByOrderId(zone['OrderId'])
                bOrderStatus = self.RTLocalData_.orderGetStatusbyOrderId (zone['OrderId'])
                bSLOrderError = False
                bSLOrderExists = self.RTLocalData_.orderCheckIfExistsByOrderId(zone['OrderIdSL'])
                bSLOrderStatus = self.RTLocalData_.orderGetStatusbyOrderId (zone['OrderIdSL'])
                bTPOrderError = False
                bTPOrderExists = self.RTLocalData_.orderCheckIfExistsByOrderId(zone['OrderIdTP'])
                bTPOrderStatus = self.RTLocalData_.orderGetStatusbyOrderId (zone['OrderIdTP'])
                if zone['OrderIdSL'] == None or not bSLOrderExists or bSLOrderStatus in orderInactiveStatus:
                    bSLOrderError = True
                if zone['OrderIdTP'] == None or not bTPOrderExists or bTPOrderStatus in orderInactiveStatus:
                    bTPOrderError = True

                # Ahora vemos qué se hace por cada error
                #

                if bSLOrderError and bTPOrderError:   # está mal. Las condiciones hay que ponerlas bien
                    if (datetime.datetime.now() - currentSymbolStrategy['timelasterror']) < Error_orders_timer_dt:
                        continue

                    new_zone = self.strategyPentagramaRuCreateBracketOrder (currentSymbolStrategy, zone)
                    if new_zone != None:
                        currentSymbolStrategy['zones'][iter] = new_zone   # Actualiza la zona
                        bStrategyUpdated = True
                        currentSymbolStrategy['ordersUpdated'] = True
                    else:
                        currentSymbolStrategy['timelasterror'] = datetime.datetime.now()
                        self.strategyPentagramaRuUpdate (currentSymbolStrategy)
            
            if bStrategyUpdated:
                self.strategyPentagramaRuUpdate (currentSymbolStrategy)

    def strategyPentagramaRuReadFile (self):
        with open('strategies/RU_Pentagrama.conf') as f:
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
                
                logging.info ('############## %s', zone)
                zones.append(zone)

            elif fields[0].strip() == '%':
                zones = sorted(zones, key=lambda d: d['Price'], reverse=True)
                ahora = datetime.datetime.now() - datetime.timedelta(seconds=15)
                lineFields = {'symbol': lineSymbol, 'stratEnabled': lineStratEnabled, 'currentPos': lineCurrentPos, 'zones': zones, 'zonesNOP': zones, 'timelasterror': ahora}
                lineFields['ordersUpdated'] = True
                if not bError:
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

        self.strategyList_ = lstrategyList

        return 

    def strategyPentagramaRuUpdate (self, currentSymbolStrategy):  
        lines = []
        header = '# Symbol        , En, CurrPos, \n'
        lines.append(header)
        header = '# B/S,Price,qty,PrecioSL,PrecioTP,OrdId,OrdPermId,OrdIdSL,OrdPermIdSL,OrdIdTP,OrdPermIdTP,\n'
        lines.append(header)
        lines.append(header)
        lines.append(header)
        for strategyItem in self.strategyList_:
            if strategyItem['symbol'] == currentSymbolStrategy['symbol']:
                strategyItem = currentSymbolStrategy
            line = str(strategyItem['symbol']) + ','
            line += 'True,' if strategyItem['stratEnabled'] == True else 'False,'
            line += ' \n' if strategyItem['currentPos'] == None else str(int(strategyItem['currentPos'])) + '\n'
            lines.append(line)
            for zone in strategyItem['zones']:
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
                line += str(zone['OrderPermIdTP'])
                lines.append(line)
            line = '%'
            lines.append(line)

        with open('strategies/RU_Pentagrama.conf', 'w') as f:
            for line in lines:
                f.writelines(line)

    def strategyPentagramaRuOrderUpdated (self, symbol, data):

        currentSymbolStrategy = None
        for symbolStrategy in self.strategyList_:
            if symbolStrategy['symbol'] == symbol:
                currentSymbolStrategy = symbolStrategy
                break
        
        if currentSymbolStrategy == None:
            return

        if currentSymbolStrategy['stratEnabled'] == False:
            return

        ordenObj = data['orderObj']
        if ordenObj != "":
            self.strategyPentagramaRuOrderIdUpdated (currentSymbolStrategy, ordenObj)

    def strategyPentagramaRuOrderIdUpdated (self, currentSymbolStrategy, ordenObj):
        symbol = currentSymbolStrategy['symbol']
        bChanged = False
        for zone in currentSymbolStrategy['zones']:
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
            currentSymbolStrategy['ordersUpdated'] = True
            self.strategyPentagramaRuUpdate (currentSymbolStrategy)

    def strategyPentagramaRuCreateBracketOrder (self, currentSymbolStrategy, zone):

        symbol = currentSymbolStrategy['symbol']
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
