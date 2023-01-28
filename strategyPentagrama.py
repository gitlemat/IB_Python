import logging
import datetime
import pandasDB


logger = logging.getLogger(__name__)
Error_orders_timer_dt = datetime.timedelta(seconds=90)

    

#######################
# Pentagrama
#######################

# strategyList_:
#     'symbol'
#     'currentPos'
#     'lastCurrentZone'  
#     'lastCurrentZoneBufferPriceUp'     esta es para poder presentarlo bien en wl webFE
#     'lastCurrentZoneBufferPriceDown'  
#     'stratEnabled'
#     'cerrarPosiciones'
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

    def __init__(self, RTlocalData):
        self.RTLocalData_ = RTlocalData
        self.strategyList_ = []
        
        try:
            logging.info('Leyendo el archivo de estrategia de HE Pentagrama:')
            self.strategyList_ = self.strategyPentagramaReadFile()
            logging.info('     %s', self.strategyList_)
        except Exception as error:
            logging.error (' ')
            logging.error (' ')
            logging.error ('Error al cargar el fichero strategies/HE_Mariposa_Verano.conf')
            logging.error (' ')
            logging.error (' ')
            logging.exception(error)
            # Print un error al cargar 

    def strategyPentagramaGetAll(self):
        return self.strategyList_

    def strategyPentagramaGetStrategyBySymbol(self, symbol):
        for estrategia in self.strategyList_:
            lsymbol = estrategia['symbol']
            if lsymbol == symbol:
                return estrategia
        return None

    def strategyPentagramaGetStrategyByOrderId(self, orderId):
        for estrategia in self.strategyList_:
            lsymbol = estrategia['symbol']
            if estrategia['UpperOrderId'] == orderId or estrategia['LowerOrderId'] == orderId:
                return {'strategy':'PentagramaHE', 'symbol':lsymbol}
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
                    if current_zone_n == None:
                        logging.error ('Hay algun problema identificando la zona de %s por posiciones', symbol)
                        current_zone_n = self.strategyPentagramaGetCurrentZoneByPrice(currentSymbolStrategy, current_prices_last) 
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

            if fields[2].strip() == '' or fields[2].strip() == '0' or fields[2].strip() == 'False' :
                lineCerrarPosiciones = False
            else:
                lineCerrarPosiciones = True

            if fields[3].strip() == '' or fields[2].strip() == 'None':
                lineUpperOrderId = None
            elif fields[3].strip() == 'KO':
                lineUpperOrderId = 'KO'
            else:
                lineUpperOrderId = int (fields[3].strip())

            if fields[4].strip() == ''  or fields[4].strip() == 'None':
                lineUpperOrderPermId = None
            else:
                lineUpperOrderPermId = int (fields[4].strip())

            if fields[5].strip() == ''  or fields[5].strip() == 'None':
                lineLowerOrderId = None
            else:
                lineLowerOrderId = int (fields[5].strip())

            if fields[6].strip() == ''  or fields[6].strip() == 'None':
                lineLowerOrderPermId = None
            else:
                lineLowerOrderPermId = int (fields[6].strip())

            if fields[7].strip() == '':
                lineCurrentPos = None   
            else:
                lineCurrentPos = int (fields[7].strip())

            if fields[8].strip() == '':
                lineOverlapMargin = 0
            else:
                lineOverlapMargin = float (fields[8].strip())

            nField = 9
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

            #lineFields = {'symbol': lineSymbol, 'stratEnabled': lineStratEnabled, 'cerrarPosiciones': lineCerrarPosiciones,'currentPos': lineCurrentPos, 'lastCurrentZone': None, 'lastCurrentZoneBufferPriceUp': None, 'lastCurrentZoneBufferPriceDown': None, 'UpperOrderId': lineUpperOrderId, 'UpperOrderPermId': lineUpperOrderPermId, 'LowerOrderId': lineLowerOrderId, 'LowerOrderPermId': lineLowerOrderPermId, 'OverlapMargin': lineOverlapMargin, 'zones': zones, 'zonesNOP': zones, 'timelasterror': ahora}
            lineFields = {}
            lineFields['symbol'] = lineSymbol
            lineFields['stratEnabled'] = lineStratEnabled
            lineFields['cerrarPosiciones'] = lineCerrarPosiciones
            lineFields['currentPos'] = lineCurrentPos
            lineFields['lastCurrentZone'] = None
            lineFields['lastCurrentZoneBufferPriceUp'] = None
            lineFields['lastCurrentZoneBufferPriceDown'] = None
            lineFields['UpperOrderId'] = lineUpperOrderId
            lineFields['UpperOrderPermId'] = lineUpperOrderPermId
            lineFields['LowerOrderId'] = lineLowerOrderId
            lineFields['LowerOrderPermId'] = lineLowerOrderPermId
            lineFields['OverlapMargin'] = lineOverlapMargin
            lineFields['zones'] = zones
            lineFields['zonesNOP'] = zones
            lineFields['timelasterror'] = ahora
            lineFields['dbPandas'] = pandasDB.dbPandasStrategy (lineSymbol, 'Pentagrama', self.RTLocalData_.influxIC_)  
            #zonesNOP sirve como No Operativa. Por si queremos hacer cambios con confirmacion
            lineFields['ordersUpdated'] = True
            lstrategyList.append(lineFields)

        logging.info ('Estrategias Pentagrama cargadas')

        return lstrategyList

    def strategyPentagramaGetCurrentZoneByPos (self, currentSymbolStrategy):
        nPos = currentSymbolStrategy['currentPos']
        current_zone_n = None
        for zone_n in range(len(currentSymbolStrategy['zones'])):
            if currentSymbolStrategy['zones'][zone_n]['reqPos'] == nPos:
                current_zone_n = zone_n  
        if current_zone_n != None: 
            logging.info('La estrategia %s está en zona: %d', currentSymbolStrategy['symbol'], current_zone_n)
        else:
            logging.error('La estrategia %s está fuera de todas las zonas (pos: %d)', currentSymbolStrategy['symbol'], nPos)
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
            line += 'True,' if strategyItem['cerrarPosiciones'] == True else 'False,'
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
        
                    newreqId = self.RTLocalData_.orderPlaceBrief (symbol, secType, action, oType, mktPrice, qty) #Orden de Upper limit
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

    
    def strategyPentagramaOrderExecuted (self, symbol, data):
        executionObj = data['executionObj']
        exec_contract = data['contractObj']

        # Primero se lo lanzamos a strategyPentagramaOrderFilled por si IB nos manda solo el Exec y no el Filled

        currentSymbolStrategy = None
        for symbolStrategy in self.strategyList_:
            if symbolStrategy['symbol'] == symbol:
                currentSymbolStrategy = symbolStrategy
                break

        if currentSymbolStrategy == None:
            return

        if currentSymbolStrategy['stratEnabled'] == False:
            return

        orderId = executionObj.orderId
        order = self.RTLocalData_.orderGetByOrderId(orderId) # Nos va a dar su permId que usaremos para los datos guardados

        self.strategyPentagramaOrderFilled (currentSymbolStrategy, order) 

        # Aquí ya solo nos centramos en mandarlo a Influx

        logging.debug ('Order Executed:')
        logging.debug ('  Symbol: %s (%s)', exec_contract.symbol, exec_contract.secType)
        logging.debug ('  ExecId: %s', executionObj.execId)
        logging.debug ('  OrderId/PermId: %s/%s', executionObj.orderId, executionObj.permId)
        logging.debug ('  Number/Price: %s at %s', executionObj.shares, executionObj.price)
        logging.debug ('  Cumulative: %s', executionObj.cumQty)
        logging.debug ('  Liquidity: %s',executionObj.lastLiquidity)
        
        gConId = order['contractId']
        contract = self.RTLocalData_.contractGetContractbyGconId(gConId)

        lRemaining = order['order'].totalQuantity - executionObj.cumQty

        if lRemaining > 0:
            return

        numLegs = len(contract['contractReqIdLegs'])
        contract_secType = contract['contract'].secType
        exec_secType = exec_contract.secType     # Solo guardamos las de la BAG (o el que sea el que lancé)

        data_new = {}
        data_new['ExecId'] = executionObj.execId
        data_new['OrderId'] = executionObj.orderId
        data_new['PermId'] = executionObj.permId
        data_new['Quantity'] = executionObj.cumQty
        data_new['Side'] = executionObj.side
        data_new['numLegs'] = numLegs
        data_new['contractSecType'] = contract_secType
        data_new['execSecType'] = exec_secType

        # currentSymbolStrategy['dbPandas'].dbAddExecOrder(data_new)
        # Aquí se para y borra lo de abajo

        if contract_secType != exec_secType:
            return False

        records = []
        record = {}
        fields = {}
        tags = {'symbol': symbol, 'strategy': 'Pentagrama'}
        time = datetime.datetime.now()
        
        fields['ExecId'] = executionObj.execId
        fields['OrderId'] = executionObj.orderId
        fields['PermId'] = executionObj.permId
        fields['Quantity'] = executionObj.cumQty
        fields['Side'] = executionObj.side

        record = {
            "measurement": "executions", 
            "tags": tags,
            "fields": fields,
            "time": time,
        }
        records.append(record)

        self.RTLocalData_.influxIC_.write_data(records)

    def strategyPentagramaOrderCommission (self, data):
        ExecId = data['CommissionReport'].execId
        currentSymbolStrategy = None
        for symbolStrategy in self.strategyList_:
            if symbolStrategy['dbPandas'].dbCheckIfExecIdInStrategy(ExecId) == True:
                currentSymbolStrategy = symbolStrategy
                break

        if currentSymbolStrategy == None:
            return

        if currentSymbolStrategy['stratEnabled'] == False:
            return

        currentSymbolStrategy['dbPandas'].dbAddCommissionsOrder(data['CommissionReport'])

    # Al principio las border orders solo tienen el ordenId, con esto se pone el permId en cuanto llega de IB
    # Pero tambien sirve para actualizar la orderId usandp la permId

    def strategyPentagramaOrderUpdated (self, symbol, data):

        # Primero miramos si el simbolo pertenece a esta strategia
        currentSymbolStrategy = None
        for symbolStrategy in self.strategyList_:
            if symbolStrategy['symbol'] == symbol:
                currentSymbolStrategy = symbolStrategy
                break
        
        if currentSymbolStrategy == None:
            return

        if currentSymbolStrategy['stratEnabled'] == False:
            return

        # Ahora miramos si hay que actualizar los orderID/permId

        ordenObj = data['orderObj']
        if ordenObj != "":
            self.strategyPentagramaOrderIdUpdated (currentSymbolStrategy, ordenObj)

        # Y Ahora miramos si hay un cambio de estado.

        orderId = data['orderId']
        order = self.RTLocalData_.orderGetByOrderId(orderId) # Nos va a dar su permId que usaremos para los datos guardados

        if not order:
            logging.error ('Error leyendo la orderId %s', str(orderId))
            return

        if not 'status' in order['params']:
            return
        
        orderStatus = order['params']['status']   # Ya está actualizado por el Local_Daemon justo antes de llamar a estrategia

        if orderStatus == 'Filled':
            self.strategyPentagramaOrderFilled (currentSymbolStrategy, order)
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
        elif currentSymbolStrategy['UpperOrderPermId'] == ordenObj.permId and currentSymbolStrategy['UpperOrderId'] != ordenObj.orderId:  # Esto es por si el orderId cambia (el permId no puede cambiar)
            logging.info ('Orden actualizada en estrategia (o inicializamos) %s. Nueva UpperOrderId: %s', symbol, ordenObj.orderId)
            currentSymbolStrategy['UpperOrderId'] = ordenObj.orderId
            bChanged = True
        elif currentSymbolStrategy['LowerOrderPermId'] == ordenObj.permId and currentSymbolStrategy['LowerOrderId'] != ordenObj.orderId:
            logging.info ('Orden actualizada en estrategia (o inicializamos)  %s. Nueva LowerOrderId: %s', symbol, ordenObj.orderId)
            currentSymbolStrategy['LowerOrderId'] = ordenObj.orderId
            bChanged = True
        
        if bChanged:
            currentSymbolStrategy['ordersUpdated'] = True
            self.strategyPentagramaUpdate (currentSymbolStrategy)
                
    def strategyPentagramaOrderFilled (self, currentSymbolStrategy, order):
        
        # La exec trae el order_id que use para cargar el contrato asociado
        orderId = order['order'].orderId
        orderPermId = order['order'].permId    
        
        gConId = order['contractId']
        contract = self.RTLocalData_.contractGetContractbyGconId(gConId)
 
        symbol = currentSymbolStrategy['symbol']
    
        kickOff = False
        if currentSymbolStrategy['UpperOrderId'] == 'KO':
            kickOff = True

        if order['Executed'] == True:   # Ya la hemos evaluado
            return

        logging.info ('Orden ejecutada en estrategia %s. OrderId: %s', symbol, orderId)

        if kickOff and orderId != currentSymbolStrategy['LowerOrderId']:
            return False

        if (not kickOff) and (orderPermId != currentSymbolStrategy['LowerOrderPermId']) and (orderPermId != currentSymbolStrategy['UpperOrderPermId']):
            return False # No es ninguna orden de nuestra estrategia
        
        lRemaining = int(order['params']['remaining'])
        if lRemaining > 0:
            logging.info ('     Nos faltan %d shares por ejecutar en la orden (%s)', lRemaining, orderId)
            return # Volverá

        lAccion = ''
        # Llevo un tracking de las posiciones de la estrategia. Solo considero las que meto yo.
        if order['order'].action == 'BUY':                  #delta_pos es el impacto de la orden que se acaba de ejecutar
            lAccion = 'comprado'
            delta_pos = order['params']['filled']
        else:
            lAccion = 'vendido'
            delta_pos = (-1) * order['params']['filled']
        currentSymbolStrategy['currentPos'] += delta_pos  # La posición va a ser la que tenía más el cambio
        logging.info ('     Hemos %s %d posiciones. Ahora tenemos %d', lAccion, delta_pos, currentSymbolStrategy['currentPos'])
        
        self.RTLocalData_.orderSetExecutedStatus (orderId, True)    # La marcamos como Executed

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

        
    def strategyPentagramaOrderCancelled (self, currentSymbolStrategy, order):
        
        orderId = order['order'].orderId
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

        bUpperPermExists = self.RTLocalData_.orderCheckIfExistsByOrderPermId(currentSymbolStrategy['UpperOrderPermId'])
        bUpperPermStatus = self.RTLocalData_.orderGetStatusbyOrderPermId (currentSymbolStrategy['UpperOrderPermId'])
            
        bLowerPermExists = self.RTLocalData_.orderCheckIfExistsByOrderPermId(currentSymbolStrategy['LowerOrderPermId'])
        bLowerPermStatus = self.RTLocalData_.orderGetStatusbyOrderPermId (currentSymbolStrategy['LowerOrderPermId'])

        # Aqui ya sabemos que no es kickoff, y se ha cancelado una border.
        # No cancelo todas ciegamente por si se ha cancelado de alguna manera rara
        logging.info ('    Generamos los bordes' )
        if orderPermId == currentSymbolStrategy['UpperOrderPermId']:
            currentSymbolStrategy['LowerOrderPermId'] = None
            currentSymbolStrategy['LowerOrderId'] = None
            if bLowerPermExists and bLowerPermStatus not in ['PreSubmitted', 'PendingSubmit', 'Submitted']: 
                currentSymbolStrategy['UpperOrderPermId'] = None
                currentSymbolStrategy['UpperOrderId'] = None

        if orderPermId == currentSymbolStrategy['LowerOrderPermId']:
            currentSymbolStrategy['UpperOrderPermId'] = None
            currentSymbolStrategy['UpperOrderId'] = None
            if bUpperPermExists and bUpperPermStatus not in ['PreSubmitted', 'PendingSubmit', 'Submitted']:
                currentSymbolStrategy['LowerOrderPermId'] = None
                currentSymbolStrategy['LowerOrderId'] = None
        
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
            newreqUpId = self.RTLocalData_.orderPlaceBrief (symbol, secType, action, oType, lmtPrice, qty) #Orden de Upper limit
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
            newreqDownId = self.RTLocalData_.orderPlaceBrief (symbol, secType, action, oType, lmtPrice, qty)  #Orden de Lower
            if newreqDownId == None:
                currentSymbolStrategy['LowerOrderId'] = None   # En el loop saltara que falta un leg y volverá aquí.
            else:
                currentSymbolStrategy['LowerOrderId'] = newreqDownId
            currentSymbolStrategy['LowerOrderPermId'] = None
    
        # Actualizar fichero con nuevas ordenes limite
        currentSymbolStrategy['ordersUpdated'] = True
        return currentSymbolStrategy