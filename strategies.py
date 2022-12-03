import logging
import datetime


logger = logging.getLogger(__name__)
Error_orders_timer_dt = datetime.timedelta(seconds=90)

class Strategies():

    def __init__(self, RTlocalData, appObj):
        self.RTLocalData_ = RTlocalData
        self.appObj_ = appObj
        #self.strategyIndex_ = []

        self.RTLocalData_.strategies_ = self
        
        self.strategyPentagramaObj_ = strategyPentagrama(self.RTLocalData_, self.appObj_)

        #self.strategyIndexReadFile()

    '''
    def strategyIndexReadFile(self):
        with open('strategies/strategyIndex.conf') as f:
            lines = f.readlines()
    
        for line in lines:
            lfields = line.split(',')
            lineSymbol = lfields[0].strip()
            lineStrategy = lfields[1].strip()
            ldata = {'symbol': lineSymbol, 'strategyFile': lineStrategy}
            self.strategyIndex_.append(ldata)
    '''

    '''
    def strategyIndexGetStrategyBySymbol (self, symbol):
        strategy = None
        for item in self.strategyIndex_:
            if item['symbol'] == symbol:
                strategy = item['strategyFile']
                break    
        return strategy
    

    def strategyIndexCheckIfEnabled (self, symbol):
        enabled = False
        for item in self.strategyIndex_:
            if item['symbol'] == symbol:
                if item['strategyFile'] == 'EstrategiaPentagrama':
                    enabled = self.strategyPentagramaObj_.strategyPentagramaCheckEnabled (symbol)  
                break
        return enabled
    '''

    # EN el loop. Esta es la maestra que mira que todos los contratos del Index tienen bien todo
    def strategyIndexCheckAll (self):
        self.strategyPentagramaObj_.strategyPentagramaLoopCheck ()
        '''
        for item in self.strategyIndex_:
            if item['strategyFile'] == 'EstrategiaPentagrama':
                self.strategyPentagramaObj_.strategyPentagramaLoopCheck (item['symbol'])
        '''
    
    # Para cuando haya que actualizar las ordenes (de orderId a PermId)
    def strategyIndexOrderUpdate (self, data):

        orderId = data['orderId']
        order = self.RTLocalData_.orderGetByOrderId(orderId) # Nos va a dar su permId que usaremos para los datos guardados        
        if not order:
            return
        gConId = order['contractId'] 
        symbol = self.RTLocalData_.contractSummaryBrief(gConId)

        self.strategyPentagramaObj_.strategyPentagramaOrderUpdated (symbol, data)  # Si defino mas ordenes, añado lineas como esta

        '''

        if not self.strategyIndexCheckIfEnabled (symbol):
            return

        for item in self.strategyIndex_:
            if item['symbol'] == symbol:  # Que la orden sea de este contrato
                if item['strategyFile'] == 'EstrategiaPentagrama':
                    self.strategyPentagramaObj_.strategyPentagramaOrderUpdated (symbol, data)
        '''

    '''
    # Se ha ejecutado una orden y hay que ver si corresponde a alguna estrategia
    def strategyIndexOrderExecuted (self, data):
        executionObj = data ['executionObj']
        orderId = executionObj.orderId
        logging.info ('Orden Ejecutada : %d', orderId)
        order = self.RTLocalData_.orderGetByOrderId(orderId) # Nos va a dar su permId que usaremos para los datos guardados        
        gConId = order['contractId'] 
        symbol = self.RTLocalData_.contractSummaryBrief(gConId)

        if not self.strategyIndexCheckIfEnabled (symbol):
            return

        for item in self.strategyIndex_:
            if item['symbol'] == symbol:  # Que la orden sea de este contrato
                if item['strategyFile'] == 'EstrategiaPentagrama':
                    self.strategyPentagramaObj_.strategyPentagramaOrderExecuted (data)
        
    '''

#######################
# HE Verano
#######################

# strategyList_:
#     'symbol'
#     'currentPos'
#     'lastCurrentZone'  
#     'lastCurrentZoneBufferPriceUp'     esta es para poder presentarlo bien en wl webFE
#     'lastCurrentZoneBufferPriceDown'  
#     'stratEnabled'
#     'UpperOrderId'
#     'UpperOrderPermId'
#     'LowerOrderId'
#     'LowerOrderPermId'
#     'zones': 
#         'reqPos'
#         'limitUp'
#         'limitDown'
#     'timelasterror'
# Si UpperOrderId = 'KO', el LowerOrderId es el orderId

# File:
# HEM3-2HEN3+HEQ3,,,,,,  -7,    1.5,-0.75,-4, -0.75,-1.25, 0,   -1.25,   -2, 4,-2,-2.75, 7, -2.75,   -4 

# En cada loop:
#     - Si no hay ninguna border orden, y pos=None -> Trigguer de kickoff (ver arriba)
#     - Si el lastCurrentZone == None se busca. Luego se actualiza cada vez que se ejecuta una orden, o se crean borders
#     - Si falta alguna border orden -> recrear border orders si no existen
#
# KickOff (lo lanza el loop):
#     - Al empezar solo tenemos symbol y zones
#     - Se lanza la primera orden para que tengamos elnumero de posiciones segun la zona que esté el precio
#     - En UpperOrderId = 'KO', y LowerOrderId tiene el OrderId de la primera posición
#     - Cuando esta orden se ejecute, se analiza abajo
#
# En cada orden ejecutada (order update Filled):
#     - Si UpperOrderId = KO -> Estamos en Kickoff (LowerOrderId tiene el OrderId de la primera posición)
#     - Si la orderId ejecutada coincide con el de algun border:
#         - Se asume que el numero de posiciones ha cambiado ya al ejecutarse la orden
#         - Se actualizan los border_orders segun nueva zona:
#               - Si fuimos hacia arriba:
#                    - Ordeno cancelar la antigua de abajo
#                    - Cuando reciba la confirmacion de canceacion (abajo) creo las border
#               - Si fuimos hacia abajo:
#                    - Lo mismo pero alreves
#
# Orden cancelada
#     - Busco si es la de una border.
#     - Esto quire decir que ya puedo crear las border que faltan
#     - Si estoy en KO, tengo que empezar de cero
#
# Cada actualización de orden:
#     - Se mira si es de mi simbolo. Si no no entra
#     - Si no tengo permId, lo copio si coincide el ordenId
#     - Si tengo permId y coincide con el de la orden: actualizo el orderId

# Implementacion 1

class strategyPentagrama():
## HE Summer

    def __init__(self, RTlocalData, appObj):
        self.RTLocalData_ = RTlocalData
        self.appObj_ = appObj
        self.strategyList_ = []
        
        try:
            self.strategyList_ = self.strategyPentagramaReadFile()
            logging.info('Leidas todas las estrategias (22-track):')
            logging.debug('%s', self.strategyList_)
        except:
            logging.error ('Error al cargar el fichero strategies/HE_Mariposa_Verano.conf')
            # Print un error al cargar 

    def strategyPentagramaGetAll(self):
        return self.strategyList_

    def strategyPentagramaGetStrategyBySymbol(self, symbol):
        for estrategia in self.strategyList_:
            lsymbol = estrategia['symbol']
            if lsymbol == symbol:
                return estrategia
        return None
    

    def strategyPentagramaEnableDisable (self, symbol, state):
        for symbolStrategy in self.strategyList_:
            if symbolStrategy['symbol'] == symbol:
                symbolStrategy['stratEnabled'] = state
                self.strategyPentagramaUpdate (symbolStrategy)
                break

    def strategyPentagramaCheckEnabled (self, symbol):
        # Devolver si está habilidata o no 
        enabled = False
        for symbolStrategy in self.strategyList_:
            if symbolStrategy['symbol'] == symbol:
                enabled = symbolStrategy['stratEnabled']
                break

        return enabled

    def strategyPentagramaLoopCheck (self): 
        
        for currentSymbolStrategy in self.strategyList_:
            error = 0 
            if currentSymbolStrategy['stratEnabled'] == False:
                # MISSING: habria que comprobar que no hay border orders y borrarlas.
                continue

            symbol = currentSymbolStrategy['symbol']
            contract = self.RTLocalData_.contractGetBySymbol(symbol)
    
            # Miro a ver si tenemos la zona actual
            if currentSymbolStrategy['lastCurrentZone'] == None or \
                currentSymbolStrategy['lastCurrentZoneBufferPriceUp'] == None or \
                currentSymbolStrategy['lastCurrentZoneBufferPriceDown'] == None:
                error += 10
            
            # Ahora localizar si tenemos las ordenes de arriba y abajo
            if (currentSymbolStrategy['UpperOrderPermId'] == None) and (currentSymbolStrategy['UpperOrderId'] == None):
                #logging.error('No tengo la Upper Order de %s', symbol)
                # Hace falta generar la Upper
                error += 100
            elif (currentSymbolStrategy['UpperOrderPermId'] != None) and (not self.RTLocalData_.orderCheckIfExistsByOrderPermId(currentSymbolStrategy['UpperOrderPermId'])):
                # Esto significa que la orden ha desaparecido. Esto necesita un error fuerte!!!!
                #logging.error('La Upper Order de %s (orderId: %s) ya no existe', symbol, str(currentSymbolStrategy['UpperOrderPermId']))
                error += 100
            elif self.RTLocalData_.orderGetStatusbyOrderId (currentSymbolStrategy['UpperOrderId']) == 'Cancelled':
                error += 100
    
            if (currentSymbolStrategy['LowerOrderPermId'] == None) and (currentSymbolStrategy['LowerOrderId'] == None):
                #logging.error('No tengo la Lower Order de %s', symbol)
                error += 200
            elif (currentSymbolStrategy['LowerOrderPermId'] != None) and (not self.RTLocalData_.orderCheckIfExistsByOrderPermId(currentSymbolStrategy['LowerOrderPermId'])):
                # Esto significa que la orden ha desaparecido. Esto necesita un error fuerte!!!!
                #logging.error('La Lower Order de %s (orderId: %s) ya no existe', symbol, str(currentSymbolStrategy['LowerOrderPermId']))
                error += 200
            elif self.RTLocalData_.orderGetStatusbyOrderId (currentSymbolStrategy['LowerOrderId']) == 'Cancelled':
                error += 200
    
            if currentSymbolStrategy['currentPos'] == None:   # None es solo al principio (KO), despues puede ser 0 pero no None
                error += 1000 
            
            # Ahora arreglamos lo que sea
            # Este implica que solo nos falta la current_zone
            #logging.error ('Errores totales: %d', error)
            if error > 10:
                if (datetime.datetime.now() - currentSymbolStrategy['timelasterror']) < Error_orders_timer_dt:
                    continue
            if 0 < error <= 10:
                if currentSymbolStrategy['UpperOrderId'] == 'KO':
                    continue
                current_prices_last = contract['currentPrices']['LAST']  
                logging.info ('No tengo current zone en %s', symbol)
                if not current_prices_last:
                    logging.info ('No tengo LAST price en %s', symbol)
                    #currentSymbolStrategy['timelasterror'] = datetime.datetime.now()
                    #self.strategyPentagramaUpdate (currentSymbolStrategy)
                else:
                    # Ya está el KO hecho y todo. Si falta esto, lo pillo de Pos
                    current_zone_n = self.strategyPentagramaGetCurrentZoneByPos(currentSymbolStrategy)
                    if current_zone_n != None:
                        price_Upper, price_Lower = self.strategyPentagramaGetBorderPrices (currentSymbolStrategy, current_zone_n)
                        currentSymbolStrategy['lastCurrentZone'] = current_zone_n
                        currentSymbolStrategy['lastCurrentZoneBufferPriceUp'] = price_Upper
                        currentSymbolStrategy['lastCurrentZoneBufferPriceDown'] = price_Lower
                        logging.info ('Zona de %s recuperada: %d', symbol, current_zone_n)
                    else:
                        logging.error ('No se ha podido recuperar la zona de %s', symbol)
                        currentSymbolStrategy['timelasterror'] = datetime.datetime.now()
                    self.strategyPentagramaUpdate (currentSymbolStrategy)
    
            # Este indica que nos faltan las border
            if 99 < error < 1000:
                logging.error ('A la estrategia de %s le faltan borders. Error %d', symbol, error )
                n_new_zone = self.strategyPentagramaGetCurrentZoneByPos (currentSymbolStrategy)
                new_currentSymbolStrategy = self.strategyPentagramaCreateBorderOrders (contract, currentSymbolStrategy, n_new_zone)
                if new_currentSymbolStrategy != None:
                    self.strategyPentagramaUpdate (new_currentSymbolStrategy)  # Actualizo con los datos de ordenes borde que acabo de obtener
                else:
                    # deberiamos mirar que no haya posiciones, y pausar la estrategia
                    logging.error ('Fallo en loopcheck: Error al general las border orders directamente')
                    currentSymbolStrategy['timelasterror'] = datetime.datetime.now()
                    self.strategyPentagramaUpdate (currentSymbolStrategy)
                error = 0
    
            # Nos falta hacer un KO
            if error >= 1000:
                self.strategyPentagramaKickOff(symbol)

        return

    def strategyPentagramaReadFile (self):
        with open('strategies/HE_Mariposa_Verano.conf') as f:
            lines = f.readlines()

        lstrategyList = []        
        
        logging.info ('Cargando Estrategias Pentagrama')

        for line in lines[1:]: # La primera linea es el header
            fields = line.split(',')
            lineSymbol = fields[0].strip()
            
            if fields[1].strip() == '' or fields[1].strip() == '0' or fields[1].strip() == 'False' :
                lineStratEnabled = False
            else:
                lineStratEnabled = True

            if fields[2].strip() == '' or fields[2].strip() == 'None':
                lineUpperOrderId = None
            elif fields[2].strip() == 'KO':
                lineUpperOrderId = 'KO'
            else:
                lineUpperOrderId = int (fields[2].strip())

            if fields[3].strip() == ''  or fields[3].strip() == 'None':
                lineUpperOrderPermId = None
            else:
                lineUpperOrderPermId = int (fields[3].strip())

            if fields[4].strip() == ''  or fields[4].strip() == 'None':
                lineLowerOrderId = None
            else:
                lineLowerOrderId = int (fields[4].strip())

            if fields[5].strip() == ''  or fields[5].strip() == 'None':
                lineLowerOrderPermId = None
            else:
                lineLowerOrderPermId = int (fields[5].strip())

            if fields[6].strip() == '':
                lineCurrentPos = None   
            else:
                lineCurrentPos = int (fields[6].strip())

            if fields[7].strip() == '':
                lineOverlapMargin = 0
            else:
                lineOverlapMargin = float (fields[7].strip())

            nField = 8
            zones = []
            while nField < len(fields):
                zone = {'reqPos':int(fields[nField].strip()), 'limitUp': float(fields[nField+1].strip()), 'limitDown': float(fields[nField+2].strip())}
                nField+=3
                zones.append(zone)
            zones = sorted(zones, key=lambda d: d['limitUp'], reverse=True)
            ahora = datetime.datetime.now() - datetime.timedelta(seconds=15)

            if len(zones) < 4:
                logging.error('Estrategia %s tiene solo %d zonas. Minimo es 4',lineSymbol, len(zones))
                lineStratEnabled = False

            lineFields = {'symbol': lineSymbol, 'stratEnabled': lineStratEnabled, 'currentPos': lineCurrentPos, 'lastCurrentZone': None, 'lastCurrentZoneBufferPriceUp': None, 'lastCurrentZoneBufferPriceDown': None, 'UpperOrderId': lineUpperOrderId, 'UpperOrderPermId': lineUpperOrderPermId, 'LowerOrderId': lineLowerOrderId, 'LowerOrderPermId': lineLowerOrderPermId, 'OverlapMargin': lineOverlapMargin, 'zones': zones, 'zonesNOP': zones, 'timelasterror': ahora}
            lineFields['ordersUpdated'] = True
            #zonesNOP sirve como No Operativa. Por si queremos hacer cambios con confirmacion
            lstrategyList.append(lineFields)

        logging.info ('Estrategias Pentagrama cargadas')

        return lstrategyList

    def strategyPentagramaGetCurrentZoneByPos (self, currentSymbolStrategy):
        nPos = currentSymbolStrategy['currentPos']
        current_zone_n = None
        for zone_n in range(len(currentSymbolStrategy['zones'])):
            if currentSymbolStrategy['zones'][zone_n]['reqPos'] == nPos:
                current_zone_n = zone_n   
        #logging.info('La estrategia %s está en zona: %s (Last_Price: %.3f)', currentSymbolStrategy['symbol'], current_zone_n, current_prices_last)
        return current_zone_n
    
    def strategyPentagramaGetCurrentZoneByPrice (self, currentSymbolStrategy, current_prices_last):
        current_zone_n = None
        for zone_n in range(len(currentSymbolStrategy['zones'])):
            if currentSymbolStrategy['zones'][zone_n]['limitDown'] < current_prices_last <= currentSymbolStrategy['zones'][zone_n]['limitUp']:
                current_zone_n = zone_n
                break

        if current_zone_n != None:
            logging.info('La estrategia %s está en zona: %s (Last_Price: %.3f)', currentSymbolStrategy['symbol'], current_zone_n, current_prices_last)
        else:
            logging.error('La estrategia %s está fuera de todas las zonas (Last_Price: %.3f)', currentSymbolStrategy['symbol'], current_zone_n)
        return current_zone_n

    def strategyPentagramaGetBorderPrices (self, currentSymbolStrategy, current_zone_n):
        zoneFirst = False
        zoneLast = False
        zoneBeforeFirst = False
        zoneBeforeLast = False

        if current_zone_n == 0:
            zoneFirst = True
        if current_zone_n == 1:
            zoneBeforeFirst = True
        if current_zone_n == (len(currentSymbolStrategy['zones']) - 1):
            zoneLast = True
        if current_zone_n == (len(currentSymbolStrategy['zones']) - 2):
            zoneBeforeLast = True
        
        current_zone = currentSymbolStrategy['zones'][current_zone_n]

        # Primero el Price Uppper
        if zoneFirst:
            price_Upper = current_zone['limitUp']
        elif zoneBeforeFirst: # Como la first está muy lejos, aplicamos un buffer como si fuese zona intermedia
            # Busco distancia entre upper y lower de esta zona, y lo uso como distancia genérica
            buffer = abs(current_zone['limitUp'] - current_zone['limitDown']) * currentSymbolStrategy['OverlapMargin']
            price_Upper = current_zone['limitUp'] + buffer
        else:
            buffer = abs(currentSymbolStrategy['zones'][current_zone_n-1]['limitUp'] - current_zone['limitUp']) * currentSymbolStrategy['OverlapMargin']
            price_Upper = current_zone['limitUp'] + buffer

        # Despues el Price Lower
        if zoneLast:
            price_Lower = current_zone['limitDown']
        elif zoneBeforeLast:
            buffer = abs(current_zone['limitDown'] - current_zone['limitUp']) * currentSymbolStrategy['OverlapMargin']
            price_Lower = current_zone['limitDown'] - buffer
        else:
            buffer = abs(currentSymbolStrategy['zones'][current_zone_n+1]['limitDown'] - current_zone['limitDown']) * currentSymbolStrategy['OverlapMargin']
            price_Lower = current_zone['limitDown'] - buffer

        logging.info ('Los border prices de %s son [%f,%f]', currentSymbolStrategy['symbol'], price_Upper, price_Lower)

        return price_Upper, price_Lower


    def strategyPentagramaUpdate (self, currentSymbolStrategy):  
        lines = []
        header = '#Symbol        , En, UpOrdId, UpOrdPermId, LoOrdId, LoOrdPermId, CurrPos, Overlap, [reqPos, limUp, limDo, reqPos, limUp, limDo, reqPos, limUp, limDo, reqPos, limUp, limDo, reqPos, limUp, limDo]\n'
        lines.append(header)
        for strategyItem in self.strategyList_:
            if strategyItem['symbol'] == currentSymbolStrategy['symbol']:
                strategyItem = currentSymbolStrategy
            line = str(strategyItem['symbol']) + ','
            line += 'True,' if strategyItem['stratEnabled'] == True else 'False,'
            line += ' ,' if strategyItem['UpperOrderId'] == None else str(strategyItem['UpperOrderId']) + ','
            line += ' ,' if strategyItem['UpperOrderPermId'] == None else str(strategyItem['UpperOrderPermId']) + ','
            line += ' ,' if strategyItem['LowerOrderId'] == None else str(strategyItem['LowerOrderId']) + ','
            line += ' ,' if strategyItem['LowerOrderPermId'] == None else str(strategyItem['LowerOrderPermId']) + ','
            line += ' ,' if strategyItem['currentPos'] == None else str(int(strategyItem['currentPos'])) + ','
            line += str(strategyItem['OverlapMargin']) + ','
            for zone in strategyItem['zones']:
                line += str(zone['reqPos']) + ',' + str(zone['limitUp']) + ',' + str(zone['limitDown']) + ','
            line = line [:-1] + '\n'
            lines.append(line)
        with open('strategies/HE_Mariposa_Verano.conf', 'w') as f:
            for line in lines:
                f.writelines(line)
 
    def strategyPentagramaUpdateZones (self, symbol, zones, onlyNOP=False):
        for strategyItem in self.strategyList_:
            if strategyItem['symbol'] == symbol:
                strategyItem['zonesNOP'] = zones
                if onlyNOP == False:
                    strategyItem['zones'] = zones              
                    if len(zones) < 4:
                        logging.error('Estrategia %s tiene solo %d zonas. Minimo es 4',symbol, len(zones))
                        strategyItem['stratEnabled'] = False
                    else: # Todo bien
                        contract = self.RTLocalData_.contractGetBySymbol(symbol)
                        current_prices_last = contract['currentPrices']['LAST'] 
                        if not current_prices_last:
                            logging.info ('No tengo LAST price en %s', symbol)
                        else:
                            current_zone_n = self.strategyPentagramaGetCurrentZoneByPrice(strategyItem, current_prices_last) 
                            if current_zone_n != None:
                                price_Upper, price_Lower = self.strategyPentagramaGetBorderPrices (strategyItem, current_zone_n)
                                strategyItem['lastCurrentZone'] = current_zone_n
                                strategyItem['lastCurrentZoneBufferPriceUp'] = price_Upper
                                strategyItem['lastCurrentZoneBufferPriceDown'] = price_Lower
                            else:
                                strategyItem['timelasterror'] = datetime.datetime.now()
                    self.strategyPentagramaUpdate (strategyItem)

    def strategyPentagramaKickOff (self, symbol):
        
        # No tenemos las ordenes de arriba y abajo, y quizá 
        contract = self.RTLocalData_.contractGetBySymbol(symbol)
        current_prices_last = contract['currentPrices']['LAST']  

        if not current_prices_last:
            return False

        # buscamos los datos de este contrato en concreto    
        for currentSymbolStrategy in self.strategyList_:
            if currentSymbolStrategy['symbol'] == symbol:
                logging.info ('Estrategia en kickoff: %s', symbol)
                if not currentSymbolStrategy:
                    logging.error ('Fallo en kickoff: Estrategia no encontraga')
                    return False               # Segun la logica esto no debería pasar nunca
        
                # Sacamos las zonas de esta estrategia para este contrato
                # Detectamos en qué zona estamos, y si es la primera o ultima    
                '''     
                current_zone = None
                for zone_n in range(len(currentSymbolStrategy['zones'])):
                    if currentSymbolStrategy['zones'][zone_n]['limitDown'] < current_prices_last <= currentSymbolStrategy['zones'][zone_n]['limitUp']:  
                        current_zone = currentSymbolStrategy['zones'][zone_n]
                        break
                '''
                # Como es la primera, la pillo por precio.
                current_zone_n = self.strategyPentagramaGetCurrentZoneByPrice(currentSymbolStrategy, current_prices_last)
                
                if current_zone_n == None:
                    return False# Precio fuera de rango de zones

                currentSymbolStrategy['lastCurrentZone'] = current_zone_n

                # Aquí hay que ordenar comprar o vender (depende de si es posiv o neg) y con un bracket. No sé hacerlo.
                needed_pos = currentSymbolStrategy['zones'][current_zone_n]['reqPos']
        
                newreqId = None
                secType = contract['contract'].secType
                oType = 'MKT'
                mktPrice = 0
        
                if needed_pos > 0: # La Upper sería cerrar todo
                    action = 'BUY'
                    qty = needed_pos
                if needed_pos < 0:
                    action = 'SELL'
                    qty = abs(needed_pos)
        
                if needed_pos != 0:
                    logging.info ('    Vamos a generar orden para iniciar todo con esto:')
                    logging.info ('        Action: %s', action)
                    logging.info ('        Qty: %s', str(qty))
        
                    newreqId = self.appObj_.placeOrderBrief (symbol, secType, action, oType, mktPrice, qty) #Orden de Upper limit
                    if newreqId == None:
                        logging.error ('Fallo en kickoff: Error al generar orden inicial')
                        currentSymbolStrategy['timelasterror'] = datetime.datetime.now()
                        self.strategyPentagramaUpdate (currentSymbolStrategy)
                        return False
                    # Marco con un flag(KO) en el fichero para que cuando llegue el evento lo reconozca y sepa que estamos en KickOff
                    currentSymbolStrategy['UpperOrderId'] = 'KO'
                    currentSymbolStrategy['LowerOrderId'] = newreqId 
                    currentSymbolStrategy['currentPos'] = 0
                    currentSymbolStrategy['ordersUpdated'] = True
                else: # Si es cero creo directamente las borders y quitamos el KO ya que no esperamos orden de KickOff
                    newSymbolStrategy = self.strategyPentagramaCreateBorderOrders (contract, currentSymbolStrategy, None)
                    if newSymbolStrategy == None:
                        logging.error ('Fallo en kickoff: Error al general las border orders directamente')
                        currentSymbolStrategy['timelasterror'] = datetime.datetime.now()
                        self.strategyPentagramaUpdate (currentSymbolStrategy)
                        return False
                    currentSymbolStrategy = newSymbolStrategy
                    currentSymbolStrategy['currentPos'] = 0
        
                self.strategyPentagramaUpdate (currentSymbolStrategy)
                return

    # Al principio las border orders solo tienen el ordenId, con esto se pone el permId en cuanto llega de IB
    # Pero tambien sirve para actualizar la orderId usandp la permId

    def strategyPentagramaOrderUpdated (self, symbol, data):

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
            self.strategyPentagramaOrderIdUpdated (currentSymbolStrategy, ordenObj)

        orderId = data['orderId']
        order = self.RTLocalData_.orderGetByOrderId(orderId) # Nos va a dar su permId que usaremos para los datos guardados

        if not 'status' in order['params']:
            return
        
        orderStatus = order['params']['status']   # Ya está actualizado por el Local_Daemon justo antes de llamar a estrategia

        if orderStatus == 'Filled':
            self.strategyPentagramaOrderExecuted (currentSymbolStrategy, order)
        if orderStatus == 'Cancelled':
            self.strategyPentagramaOrderCancelled (currentSymbolStrategy, order)


    def strategyPentagramaOrderIdUpdated (self, currentSymbolStrategy, ordenObj):
        symbol = currentSymbolStrategy['symbol']
        bChanged = False
        if currentSymbolStrategy['UpperOrderPermId'] == None and currentSymbolStrategy['UpperOrderId'] == ordenObj.orderId:
            logging.info ('Orden actualizada en estrategia %s. Nueva UpperOrderPermId: %s', symbol, ordenObj.permId)
            currentSymbolStrategy['UpperOrderPermId'] = ordenObj.permId
            bChanged = True
        elif currentSymbolStrategy['LowerOrderPermId'] == None and currentSymbolStrategy['LowerOrderId'] == ordenObj.orderId:
            logging.info ('Orden actualizada en estrategia %s. Nueva LowerOrderPermId: %s', symbol, ordenObj.permId)
            currentSymbolStrategy['LowerOrderPermId'] = ordenObj.permId
            bChanged = True
        elif currentSymbolStrategy['UpperOrderPermId'] == ordenObj.permId:  # Esto es por si el orderId cambia (el permId no puede cambiar)
            logging.info ('Orden actualizada en estrategia (o inicializamos) %s. Nueva UpperOrderId: %s', symbol, ordenObj.orderId)
            currentSymbolStrategy['UpperOrderId'] = ordenObj.orderId
            bChanged = True
        elif currentSymbolStrategy['LowerOrderPermId'] == ordenObj.permId:
            logging.info ('Orden actualizada en estrategia (o inicializamos)  %s. Nueva LowerOrderId: %s', symbol, ordenObj.orderId)
            currentSymbolStrategy['LowerOrderId'] = ordenObj.orderId
            bChanged = True
        
        if bChanged:
            currentSymbolStrategy['ordersUpdated'] = True
            self.strategyPentagramaUpdate (currentSymbolStrategy)
                
    def strategyPentagramaOrderExecuted (self, currentSymbolStrategy, order):
        
        # La exec trae el order_id que use para cargar el contrato asociado
        orderId = order['orderId']
        orderPermId = order['order'].permId    
        
        gConId = order['contractId']
        contract = self.RTLocalData_.contractGetContractbyGconId(gConId)
 
        symbol = currentSymbolStrategy['symbol']
    
        kickOff = False
        if currentSymbolStrategy['UpperOrderId'] == 'KO':
            kickOff = True

        logging.info ('Orden ejecutada en estrategia %s. OrderId: %s', symbol, orderId)

        if kickOff and orderId != currentSymbolStrategy['LowerOrderId']:
            return False

        if (not kickOff) and (orderPermId != currentSymbolStrategy['LowerOrderPermId']) and (orderPermId != currentSymbolStrategy['UpperOrderPermId']):
            return False # No es ninguna orden de nuestra estrategia
        

        lAccion = ''
        # Llevo un tracking de las posiciones de la estrategia. Solo considero las que meto yo.
        if order['order'].action == 'BUY':                  #delta_pos es el impacto de la orden que se acaba de ejecutar
            lAccion = 'comprado'
            delta_pos = orden['params']['filled']
        else:
            lAccion = 'vendido'
            delta_pos = (-1) * orden['params']['filled']
        currentSymbolStrategy['currentPos'] += delta_pos  # La posición va a ser la que tenía más el cambio
        logging.info ('     Hemos %s %d posiciones. Ahora tenemos %d', lAccion, delta_pos, currentSymbolStrategy['currentPos'])
         
        # Si no es Kickoff, cancelo la otra vieja que queda
        bCreateBorders = False
        if not kickOff:
            bUpperPermExists = self.RTLocalData_.orderCheckIfExistsByOrderPermId(currentSymbolStrategy['UpperOrderPermId'])
            bUpperPermStatus = self.RTLocalData_.orderGetStatusbyOrderPermId (currentSymbolStrategy['UpperOrderPermId'])
            bUpperExists = self.RTLocalData_.orderCheckIfExistsByOrderId(currentSymbolStrategy['UpperOrderId']) 
            bUpperStatus = self.RTLocalData_.orderGetStatusbyOrderId (currentSymbolStrategy['UpperOrderId'])
            
            bLowerPermExists = self.RTLocalData_.orderCheckIfExistsByOrderPermId(currentSymbolStrategy['LowerOrderPermId'])
            bLowerPermStatus = self.RTLocalData_.orderGetStatusbyOrderPermId (currentSymbolStrategy['LowerOrderPermId'])
            bLowerExists = self.RTLocalData_.orderCheckIfExistsByOrderId(currentSymbolStrategy['LowerOrderId']) 
            bLowerStatus = self.RTLocalData_.orderGetStatusbyOrderId (currentSymbolStrategy['LowerOrderId'])

            if orderPermId == currentSymbolStrategy['UpperOrderPermId']:
                if bLowerPermStatus == 'Filled':
                    bCreateBorders = True
                else:
                    logging.info ('    Cancelamos la LowerOrderId %s', currentSymbolStrategy['LowerOrderId'])
                    self.RTLocalData_.orderCancelByOrderId (currentSymbolStrategy['LowerOrderId'])         #Cancelo anterior lower limit
            if orderPermId == currentSymbolStrategy['LowerOrderPermId']:
                if bUpperPermStatus == 'Filled':
                    bCreateBorders = True
                else:
                    logging.info ('    Cancelamos la UpperOrderId %s', currentSymbolStrategy['UpperOrderId'])
                    self.RTLocalData_.orderCancelByOrderId (currentSymbolStrategy['UpperOrderId'])         #Cancelo anterior Upper limit
        else:  # Si es kickoff no no vamos a tener una cancel order que continue el proceso
            bCreateBorders = True
        
        if bCreateBorders:
            logging.info ('    Generamos los bordes' )

            n_new_zone = self.strategyPentagramaGetCurrentZoneByPos (currentSymbolStrategy)

            currentSymbolStrategy['LowerOrderPermId'] = None
            currentSymbolStrategy['LowerOrderId'] = None
            currentSymbolStrategy['UpperOrderPermId'] = None
            currentSymbolStrategy['UpperOrderId'] = None

            
            new_currentSymbolStrategy = self.strategyPentagramaCreateBorderOrders (contract, currentSymbolStrategy, n_new_zone)
    
            if new_currentSymbolStrategy != None:  # El None me viene si estamos fuera de rango. 
                self.strategyPentagramaUpdate (new_currentSymbolStrategy)
            else:
                currentSymbolStrategy['timelasterror'] = datetime.datetime.now()
                self.strategyPentagramaUpdate (currentSymbolStrategy)  # debería volver a intentarlo despues

    def strategyPentagramaOrderExecuted_Old (self, currentSymbolStrategy, data):
        # Obtenemos datos relativos a la orden.
        executionObj = data['executionObj']
        exec_contract = data['contractObj']
        
        # La exec trae el order_id que use para cargar el contrato asociado
        orderId = executionObj.orderId
        order = self.RTLocalData_.orderGetByOrderId(orderId) # Nos va a dar su permId que usaremos para los datos guardados
        orderPermId = order['order'].permId    
        
        gConId = order['contractId']
        contract = self.RTLocalData_.contractGetContractbyGconId(gConId)
 
        symbol = currentSymbolStrategy['symbol']
    
        kickOff = False
        if currentSymbolStrategy['UpperOrderId'] == 'KO':
            kickOff = True

        logging.info ('Orden ejecutada en estrategia %s. OrderId: %s', symbol, orderId)

        if kickOff and orderId != currentSymbolStrategy['LowerOrderId']:
            return False

        if (not kickOff) and (orderPermId != currentSymbolStrategy['LowerOrderPermId']) and (orderPermId != currentSymbolStrategy['UpperOrderPermId']):
            return False # No es ninguna orden de nuestra estrategia
        
        # Llega siempre una Exec global de la mariposa(BAG), y una por cada leg. Compruebo esto para solo considear la bag
        secType = contract['contract'].secType
        exec_secType = exec_contract.secType
        if secType != exec_secType:
            return False

        lAccion = ''
        # Llevo un tracking de las posiciones de la estrategia. Solo considero las que meto yo.
        if executionObj.side == 'BOT':                  #delta_pos es el impacto de la orden que se acaba de ejecutar
            lAccion = 'comprado'
            delta_pos = executionObj.shares
        else:
            lAccion = 'vendido'
            delta_pos = (-1) * executionObj.shares
        currentSymbolStrategy['currentPos'] += delta_pos  # La posición va a ser la que tenía más el cambio
        logging.info ('     Hemos %s %d posiciones. Ahora tenemos %d', lAccion, delta_pos, currentSymbolStrategy['currentPos'])

        lRemaining = order['order'].totalQuantity - executionObj.cumQty

        if lRemaining > 0:
            logging.info ('     Nos faltan %d shares por ejecutar en la orden (%s)', lRemaining, orderId)
            return  # Esperamos a que se compre todo. Seguro?????
        
        # Vamos a pillar la zona a la que vamos según las posiciones que tenemos (se supone que aqui la orden está ejecutada del todo)
        # Si no coincide, por la razon que sea, pillamos la zona por precioLast (dejamos que lo haga la funcion de create borders)

        n_new_zone = self.strategyPentagramaGetCurrentZoneByPos (currentSymbolStrategy)

        # Si no es Kickoff, cancelo la otra vieja que queda
        if not kickOff:
            if orderPermId == currentSymbolStrategy['UpperOrderPermId']:
                logging.info ('    Cancelamos la LowerOrderId %s', currentSymbolStrategy['LowerOrderId'])
                self.RTLocalData_.orderCancelByOrderId (currentSymbolStrategy['LowerOrderId'])         #Cancelo anterior lower limit
            if orderPermId == currentSymbolStrategy['LowerOrderPermId']:
                logging.info ('    Cancelamos la UpperOrderId %s', currentSymbolStrategy['UpperOrderId'])
                self.RTLocalData_.orderCancelByOrderId (currentSymbolStrategy['UpperOrderId'])         #Cancelo anterior Upper limit
        else:  # Si es kickoff no no vamos a tener una cancel order que continue el proceso
            logging.info ('    Generamos los bordes' )
            currentSymbolStrategy['LowerOrderPermId'] = None
            currentSymbolStrategy['LowerOrderId'] = None
            currentSymbolStrategy['UpperOrderPermId'] = None
            currentSymbolStrategy['UpperOrderId'] = None
            
            new_currentSymbolStrategy = self.strategyPentagramaCreateBorderOrders (contract, currentSymbolStrategy, n_new_zone)
    
            if new_currentSymbolStrategy != None:  # El None me viene si estamos fuera de rango. 
                self.strategyPentagramaUpdate (new_currentSymbolStrategy)
            else:
                currentSymbolStrategy['timelasterror'] = datetime.datetime.now()
                self.strategyPentagramaUpdate (currentSymbolStrategy)  # debería volver a intentarlo despues
        
    def strategyPentagramaOrderCancelled (self, currentSymbolStrategy, order):
        
        orderId = order['orderId']
        orderPermId = order['order'].permId    
        
        gConId = order['contractId']
        contract = self.RTLocalData_.contractGetContractbyGconId(gConId)
 
        #symbol = self.RTLocalData_.contractSummaryBrief(gConId)
        symbol = contract['fullSymbol']
    
        kickOff = False
        if currentSymbolStrategy['UpperOrderId'] == 'KO':
            kickOff = True

        logging.info ('Orden cancelada en estrategia %s. OrderId: %s', symbol, orderId)

        if kickOff and orderId != currentSymbolStrategy['LowerOrderId']:
            return False

        if (not kickOff) and (orderPermId != currentSymbolStrategy['LowerOrderPermId']) and (orderPermId != currentSymbolStrategy['UpperOrderPermId']):
            return False # No es ninguna orden de nuestra estrategia

        if kickOff: # Empezamos de cero
            currentSymbolStrategy['LowerOrderPermId'] = None
            currentSymbolStrategy['LowerOrderId'] = None
            currentSymbolStrategy['UpperOrderPermId'] = None
            currentSymbolStrategy['UpperOrderId'] = None
            currentSymbolStrategy['currentPos'] = None
            self.strategyPentagramaUpdate (currentSymbolStrategy)
            return

        n_new_zone = self.strategyPentagramaGetCurrentZoneByPos (currentSymbolStrategy)

        # Aqui ya sabemos que no es kickoff, y se ha cancelado una border.
        # No cancelo todas ciegamente por si se ha cancelado de alguna manera rara
        logging.info ('    Generamos los bordes' )
        if orderPermId == currentSymbolStrategy['UpperOrderPermId']:
            currentSymbolStrategy['LowerOrderPermId'] = None
            currentSymbolStrategy['LowerOrderId'] = None
        if orderPermId == currentSymbolStrategy['LowerOrderPermId']:
            currentSymbolStrategy['UpperOrderPermId'] = None
            currentSymbolStrategy['UpperOrderId'] = None
        
        new_currentSymbolStrategy = self.strategyPentagramaCreateBorderOrders (contract, currentSymbolStrategy, n_new_zone)

        if new_currentSymbolStrategy != None:  # El None me viene si estamos fuera de rango. 
            self.strategyPentagramaUpdate (new_currentSymbolStrategy)
        else:
            currentSymbolStrategy['timelasterror'] = datetime.datetime.now()
            self.strategyPentagramaUpdate (currentSymbolStrategy)  # dejamos el antiguo con las borders a None y nueva posicion
                                                                   # debería volver a intentarlo despues
    
    def strategyPentagramaCreateBorderOrders (self, contract, currentSymbolStrategy, nextZone = None):

        # IfNotExists se usa cuando quiero regenerar porque he perdido algun borde. Solo los genero si no existen
        symbol = currentSymbolStrategy['symbol']  
        logging.info ('Vamos a generar las border orders de %s', symbol )
        updateUpper = True
        updateLower = True
        bUpperPermExists = self.RTLocalData_.orderCheckIfExistsByOrderPermId(currentSymbolStrategy['UpperOrderPermId'])
        bUpperPermStatus = self.RTLocalData_.orderGetStatusbyOrderPermId (currentSymbolStrategy['UpperOrderPermId'])
        bUpperExists = self.RTLocalData_.orderCheckIfExistsByOrderId(currentSymbolStrategy['UpperOrderId']) 
        bUpperStatus = self.RTLocalData_.orderGetStatusbyOrderId (currentSymbolStrategy['UpperOrderId'])
        
        bLowerPermExists = self.RTLocalData_.orderCheckIfExistsByOrderPermId(currentSymbolStrategy['LowerOrderPermId'])
        bLowerPermStatus = self.RTLocalData_.orderGetStatusbyOrderPermId (currentSymbolStrategy['LowerOrderPermId'])
        bLowerExists = self.RTLocalData_.orderCheckIfExistsByOrderId(currentSymbolStrategy['LowerOrderId']) 
        bLowerStatus = self.RTLocalData_.orderGetStatusbyOrderId (currentSymbolStrategy['LowerOrderId'])
        
        if bUpperPermExists and bUpperPermStatus != 'Cancelled' and bUpperPermStatus != 'Filled':
            logging.info ('   Generando borders. No se actualiza la upper' )
            updateUpper = False
        elif bUpperExists and bUpperStatus != 'Cancelled' and bUpperStatus != 'Cancelled' and currentSymbolStrategy['UpperOrderPermId'] == None:
            #La orderId la tengo pero no me ha llegado la permId
            logging.info ('   Generando borders. No se actualiza la upper. Tenemos la odrderId y permId no ha llegado' )
            updateUpper = False
        else:
            logging.info ('   Generando borders. La upper se va a regenerar' )

        if bLowerPermExists and bLowerPermStatus != 'Cancelled' and bLowerPermStatus != 'Filled':
            logging.info ('   Generando borders. No se actualiza la Lower' )
            updateLower = False
        elif bLowerExists and bLowerStatus != 'Cancelled' and bLowerStatus != 'Filled' and currentSymbolStrategy['LowerOrderPermId'] == None:
            logging.info ('   Generando borders. No se actualiza la Lower. Tenemos la odrderId y permId no ha llegado' )
            updateLower = False
        else:
            logging.info ('   Generando borders. La Lower se va a regenerar' )

        # Llevo un tracking de las posiciones de la estrategia. Solo considero las que meto yo.
        if not currentSymbolStrategy['currentPos']:
            current_pos = 0     # Viene de KO
        else:
            current_pos = currentSymbolStrategy['currentPos']

        # Sacamos las zonas de esta estrategia para este contrato
        # Detectamos en qué zona estamos, y si es la primera o ultima
        zoneFirst = False
        zoneLast = False
        
        if nextZone != None:
            current_zone_n = nextZone
            logging.info ('   la zona me ha venido de la funcion: (%d)', nextZone)
        else:
            current_prices_last = contract['currentPrices']['LAST'] 
            if current_prices_last == None:   # no podemos hacerlo hasta no tener los precios
                logging.info ('   No tengo los ultimos precios. Me tengo que salir' )
                return None
            current_zone_n = self.strategyPentagramaGetCurrentZoneByPrice(currentSymbolStrategy, current_prices_last)

        if current_zone_n == None:
            logging.error ('Al no tener zona no podemos crear las border')
            return

        currentSymbolStrategy['lastCurrentZone'] = current_zone_n

        if current_zone_n == 0:
            zoneFirst = True
            logging.info ('   Estamos en la zona %d (Primera)',  current_zone_n)
        elif current_zone_n == (len(currentSymbolStrategy['zones']) - 1):
            zoneLast = True
            logging.info ('   Estamos en la zona %d (Ultima)',  current_zone_n)
        else:
            logging.info ('   Estamos en la zona %d',  current_zone_n)

        price_Upper, price_Lower = self.strategyPentagramaGetBorderPrices (currentSymbolStrategy, current_zone_n)

        currentSymbolStrategy['lastCurrentZoneBufferPriceUp'] = price_Upper
        currentSymbolStrategy['lastCurrentZoneBufferPriceDown'] = price_Lower

        # Identificamos las posiciones que necesitamos para ir a la zona superior o inferior
        # Solo considero las posiciones a las que hago tracking. (current_pos) Si hay más se supone que son manuales y no las considero
        if not zoneFirst:
            pos_n_Upper = currentSymbolStrategy['zones'][current_zone_n-1]['reqPos'] - current_pos
        else:
            pos_n_Upper = current_pos * (-1)

        if not zoneLast:
            pos_n_Lower = currentSymbolStrategy['zones'][current_zone_n+1]['reqPos'] - current_pos
        else:
            pos_n_Lower = current_pos * (-1)
                
        # Definimos las ordenes límite de la zona actual
        secType = contract['contract'].secType
        oType = 'LMTGTC'
        if updateUpper:
            lmtPrice = price_Upper
            if zoneFirst:
                oType = 'STPGTC'

            qty = abs(pos_n_Upper)
            if pos_n_Upper > 0:
                action = 'BUY'
            else:
                action = 'SELL'
            
            logging.info ("Vamos a abrir una order de limite up para %s", symbol)
            newreqUpId = self.appObj_.placeOrderBrief (symbol, secType, action, oType, lmtPrice, qty) #Orden de Upper limit
            if newreqUpId == None:
                currentSymbolStrategy['UpperOrderId'] = None
            else:
                currentSymbolStrategy['UpperOrderId'] = newreqUpId
            currentSymbolStrategy['UpperOrderPermId'] = None
        
        if updateLower:
            lmtPrice = price_Lower
            if zoneLast:
                oType = 'STPGTC'
            else:
                oType = 'LMTGTC'

            qty = abs(pos_n_Lower)
            if pos_n_Lower > 0:
                action = 'BUY'
            else:
                action = 'SELL'

            logging.info ("Vamos a abrir una order de limite down para %s", symbol)
            newreqDownId = self.appObj_.placeOrderBrief (symbol, secType, action, oType, lmtPrice, qty)  #Orden de Lower
            if newreqUpId == None:
                currentSymbolStrategy['LowerOrderId'] = None   # En el loop saltara que falta un leg y volverá aquí.
            else:
                currentSymbolStrategy['LowerOrderId'] = newreqDownId
            currentSymbolStrategy['LowerOrderPermId'] = None
    
        # Actualizar fichero con nuevas ordenes limite
        currentSymbolStrategy['ordersUpdated'] = True
        return currentSymbolStrategy
