import logging
import datetime


logger = logging.getLogger(__name__)
Error_orders_timer_dt = datetime.timedelta(seconds=90)

class Strategies():

    def __init__(self, RTlocalData, appObj):
        self.RTLocalData_ = RTlocalData
        self.appObj_ = appObj
        self.strategyIndex_ = []

        self.RTLocalData_.strategies_ = self
        
        self.strategyPentagramaObj_ = strategyPentagrama(self.RTLocalData_, self.appObj_)

        self.strategyIndexReadFile()

    def strategyIndexGetAll(self):
        return self.strategyIndex_

    def strategyIndexReadFile(self):
        with open('strategies/strategyIndex.conf') as f:
            lines = f.readlines()
    
        for line in lines:
            lfields = line.split(',')
            lineSymbol = lfields[0].strip()
            lineStrategy = lfields[1].strip()
            ldata = {'symbol': lineSymbol, 'strategyFile': lineStrategy}
            self.strategyIndex_.append(ldata)

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

    # EN el loop. Esta es la maestra que mira que todos los contratos del Index tienen bien todo
    def strategyIndexCheckAll (self):
        for item in self.strategyIndex_:
            if item['strategyFile'] == 'EstrategiaPentagrama':
                self.strategyPentagramaObj_.strategyPentagramaLoopCheck (item['symbol'])
    
    # Para cuando haya que actualizar las ordenes (de orderId a PermId)
    def strategyIndexOrderUpdate (self, ordenObj):

        orderId = ordenObj.orderId
        order = self.RTLocalData_.orderGetByOrderId(orderId) # Nos va a dar su permId que usaremos para los datos guardados        
        gConId = order['contractId'] 
        symbol = self.RTLocalData_.contractSummaryBrief(gConId)

        if not self.strategyIndexCheckIfEnabled (symbol):
            return

        for item in self.strategyIndex_:
            if item['symbol'] == symbol:  # Que la orden sea de este contrato
                if item['strategyFile'] == 'EstrategiaPentagrama':
                    self.strategyPentagramaObj_.strategyPentagramaOrderUpdated (symbol, ordenObj)

    # Se ha ejecutado una orden y hay que ver si corresponde a alguna estrategia
    def strategyIndexOrderExecuted (self, executionObj):
        orderId = executionObj.orderId
        order = self.RTLocalData_.orderGetByOrderId(orderId) # Nos va a dar su permId que usaremos para los datos guardados        
        gConId = order['contractId'] 
        symbol = self.RTLocalData_.contractSummaryBrief(gConId)

        if not self.strategyIndexCheckIfEnabled (symbol):
            return

        for item in self.strategyIndex_:
            if item['symbol'] == symbol:  # Que la orden sea de este contrato
                if item['strategyFile'] == 'EstrategiaPentagrama':
                    self.strategyPentagramaObj_.strategyPentagramaOrderExecuted (executionObj)
        


#######################
# HE Verano
#######################

# strategyList_:
#     'symbol'
#     'currentPos'
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
#     - Si no hay ninguna border orden, y pos=0 -> Trigguer de kickoff (ver arriba)
#     - Si falta alguna border orden -> recrear border orders si no existen
#
# KickOff (lo lanza el loop):
#     - Al empezar solo tenemos symbol y zones
#     - Se lanza la primera orden para que tengamos elnumero de posiciones segun la zona que esté el precio
#     - En UpperOrderId = 'KO', y LowerOrderId tiene el OrderId de la primera posición
#     - Cuando esta orden se ejecute, se analiza abajo
#
# En cada orden ejecutada (Executed event):
#     - Si UpperOrderId = KO -> Estamos en Kickoff (LowerOrderId tiene el OrderId de la primera posición)
#     - Si la orderId ejecutada coincide con el de algun border:
#         - Se asume que el numero de posiciones ha cambiado ya al ejecutarse la orden
#         - Se actualizan los border_orders segun nueva zona:
#               - Si fuimos hacia arriba:
#                    - Se asume que la de arriba anterior se ha ejecutado, entonces creo una nueva:
#                         - Si es dla ultima zona de pone una orden de salita total
#                    - Y cancelo la antigua de abajo
#               - Si fuimos hacia abajo:
#                    - Lo mismo pero alreves
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
        except:
            logging.error ('Error al cargar el fichero strategies/HE_Mariposa_Verano.conf')
            # Print un error al cargar 

    def strategyPentagramaGetAll(self):
        return self.strategyList_

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

    def strategyPentagramaLoopCheck (self, symbol): 
        error = 0 
        currentSymbolStrategy = None
        for symbolStrategy in self.strategyList_:
            if symbolStrategy['symbol'] == symbol:
                currentSymbolStrategy = symbolStrategy
                break
        if currentSymbolStrategy == None:
            logging.info ("La estrategia no esta definida de manera local")
            return

        if currentSymbolStrategy['stratEnabled'] == False:
            # MISSING: habria que comprobar que no hay border orders y borrarlas.
            return
        
        # Ahora localizar si tenemos las ordenes de arriba y abajo
        if (currentSymbolStrategy['UpperOrderPermId'] == None) and (currentSymbolStrategy['UpperOrderId'] == None):
            # Hace falta generar la Upper
            error += 100
        elif (currentSymbolStrategy['UpperOrderPermId'] != None) and (not self.RTLocalData_.orderCheckIfExistsByOrderPermId(currentSymbolStrategy['UpperOrderPermId'])):
            # Esto significa que la orden ha desaparecido. Esto necesita un error fuerte!!!!
            error += 100

        if (currentSymbolStrategy['LowerOrderPermId'] == None) and (currentSymbolStrategy['LowerOrderId'] == None):
            error += 200
        elif (currentSymbolStrategy['LowerOrderPermId'] != None) and (not self.RTLocalData_.orderCheckIfExistsByOrderPermId(currentSymbolStrategy['LowerOrderPermId'])):
            # Esto significa que la orden ha desaparecido. Esto necesita un error fuerte!!!!
            error += 200

        if currentSymbolStrategy['currentPos'] == None:
            error += 1000 

        # HAY QUE COMPROBAR SI DENTRO DE LA ZONA
        # Se resuelve aqui
        if 0 < error < 1000:
            if (datetime.datetime.now() - currentSymbolStrategy['timelasterror']) < Error_orders_timer_dt:
                return
            contract = self.RTLocalData_.contractGetBySymbol(symbol)
            new_currentSymbolStrategy = self.strategyPentagramaCreateBorderOrders (contract, currentSymbolStrategy, True)
            if new_currentSymbolStrategy != None:
                self.strategyPentagramaUpdate (new_currentSymbolStrategy)  # Actualizo con los datos de ordenes borde que acabo de obtener
            else:
                # deberiamos mirar que no haya posiciones, y pausar la estrategia
                logging.error ('Fallo en loopcheck: Error al general las border orders directamente')
                currentSymbolStrategy['timelasterror'] = datetime.datetime.now()
                self.strategyPentagramaUpdate (currentSymbolStrategy)
            error = 0
        if error >= 1000:
            if (datetime.datetime.now() - currentSymbolStrategy['timelasterror']) < Error_orders_timer_dt:
                return
            self.strategyPentagramaKickOff(symbol)

        return 0

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

            lineFields = {'symbol': lineSymbol, 'stratEnabled': lineStratEnabled, 'currentPos': lineCurrentPos, 'UpperOrderId': lineUpperOrderId, 'UpperOrderPermId': lineUpperOrderPermId, 'LowerOrderId': lineLowerOrderId, 'LowerOrderPermId': lineLowerOrderPermId, 'OverlapMargin': lineOverlapMargin, 'zones': zones, 'timelasterror': ahora}
            lstrategyList.append(lineFields)

        logging.info ('Estrategias Pentagrama cargadas')

        return lstrategyList

    def strategyPentagramaUpdate (self, currentSymbolStrategy):  
        lines = []
        header = '#Symbol        , En, UpOrdId, UpOrdPermId, LoOrdId, LoOrdPermId, CurrPos, Overlap, [reqPos, limUp, limDo, reqPos, limUp, limDo, reqPos, limUp, limDo, reqPos, limUp, limDo, reqPos, limUp, limDo]\n'
        lines.append(header)
        for strategyItem in self.strategyList_:
        #for i in range(len(self.strategyList_)):
            # EL currentPos hay que cuidarlo:
            strategyItem['currentPos'] = int(strategyItem['currentPos'])

            if strategyItem['symbol'] == currentSymbolStrategy['symbol']:
                strategyItem = currentSymbolStrategy
            line = str(strategyItem['symbol']) + ','
            line += 'True,' if strategyItem['stratEnabled'] == True else 'False,'
            line += ' ,' if strategyItem['UpperOrderId'] == None else str(strategyItem['UpperOrderId']) + ','
            line += ' ,' if strategyItem['UpperOrderPermId'] == None else str(strategyItem['UpperOrderPermId']) + ','
            line += ' ,' if strategyItem['LowerOrderId'] == None else str(strategyItem['LowerOrderId']) + ','
            line += ' ,' if strategyItem['LowerOrderPermId'] == None else str(strategyItem['LowerOrderPermId']) + ','
            line += ' ,' if strategyItem['currentPos'] == None else str(strategyItem['currentPos']) + ','
            line += str(strategyItem['OverlapMargin']) + ','
            for zone in strategyItem['zones']:
                line += str(zone['reqPos']) + ',' + str(zone['limitUp']) + ',' + str(zone['limitDown']) + ','
            line = line [:-1] + '\n'
            lines.append(line)
        with open('strategies/HE_Mariposa_Verano.conf', 'w') as f:
            for line in lines:
                f.writelines(line)
 
    def strategyPentagramaUpdateZones (self, symbol, zones):
        for strategyItem in self.strategyList_:
            if strategyItem['symbol'] == symbol:
                strategyItem['zones'] = zones
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
                current_zone = None
                for zone_n in range(len(currentSymbolStrategy['zones'])):
                    if currentSymbolStrategy['zones'][zone_n]['limitDown'] < current_prices_last <= currentSymbolStrategy['zones'][zone_n]['limitUp']:  
                        current_zone = currentSymbolStrategy['zones'][zone_n]
                        break
                
                if not current_zone:
                    return False# Precio fuera de rango de zones
        
                # Aquí hay que ordenar comprar o vender (depende de si es posiv o neg) y con un bracket. No sé hacerlo.
                needed_pos = current_zone['reqPos']
        
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
                    logging.info ('Vamos a generar orden con esto:')
                    logging.info ('    Action: %s', action)
                    logging.info ('    Qty: %s', str(qty))
        
                    newreqId = self.appObj_.placeOrderBrief (symbol, secType, action, oType, mktPrice, qty) #Orden de Upper limit
                    if newreqId == None:
                        logging.error ('Fallo en kickoff: Error al generar orden inicial')
                        currentSymbolStrategy['timelasterror'] = datetime.datetime.now()
                        return False
                    # Marco con un flag(KO) en el fichero para que cuando llegue el evento lo reconozca y sepa que estamos en KickOff
                    currentSymbolStrategy['UpperOrderId'] = 'KO'
                    currentSymbolStrategy['LowerOrderId'] = newreqId 
                    currentSymbolStrategy['currentPos'] = 0
                else: # Si es cero creo directamente las borders y quitamos el KO ya que no esperamos orden de KickOff
                    newSymbolStrategy = self.strategyPentagramaCreateBorderOrders (contract, currentSymbolStrategy)
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
    def strategyPentagramaOrderUpdated (self, symbol, ordenObj):
        for symbolStrategy in self.strategyList_:
            if symbolStrategy['symbol'] == symbol:
                if symbolStrategy['UpperOrderPermId'] == None and symbolStrategy['UpperOrderId'] == ordenObj.orderId:
                    logging.info ('Orden actualizada en estrategia %s. Nueva UpperOrderPermId: %s', symbol, ordenObj.permId)
                    symbolStrategy['UpperOrderPermId'] = ordenObj.permId
                if symbolStrategy['LowerOrderPermId'] == None and symbolStrategy['LowerOrderId'] == ordenObj.orderId:
                    logging.info ('Orden actualizada en estrategia %s. Nueva LowerOrderPermId: %s', symbol, ordenObj.permId)
                    symbolStrategy['LowerOrderPermId'] = ordenObj.permId

                if symbolStrategy['UpperOrderPermId'] == ordenObj.permId:  # Esto es por si el orderId cambia (el permId no puede cambiar)
                    logging.info ('Orden actualizada en estrategia %s. Nueva UpperOrderId: %s', symbol, ordenObj.orderId)
                    symbolStrategy['UpperOrderId'] = ordenObj.orderId
                if symbolStrategy['LowerOrderPermId'] == ordenObj.permId:
                    logging.info ('Orden actualizada en estrategia %s. Nueva LowerOrderId: %s', symbol, ordenObj.orderId)
                    symbolStrategy['LowerOrderId'] = ordenObj.orderId
                break


    def strategyPentagramaOrderExecuted (self, data):
        # Obtenemos datos relativos a la orden.
        executionObj = data['executionObj']
        exec_contract = data['contractObj']
        
        # La exec trae el order_id que use para cargar el contrato asociado
        orderId = executionObj.orderId
        order = self.RTLocalData_.orderGetByOrderId(orderId) # Nos va a dar su permId que usaremos para los datos guardados
        orderPermId = order['order'].permId    
        
        gConId = order['contractId']
        contract = self.RTLocalData_.contractGetContractbyGconId(gConId)
 
        symbol = self.RTLocalData_.contractSummaryBrief(gConId)
    
        # buscamos los datos de este contrato en concreto
        currentSymbolStrategy = None
        for symbolStrategy in self.strategyList_:
            if symbolStrategy['symbol'] == symbol:
                currentSymbolStrategy = symbolStrategy
                break
    
        # Un par de comrobaciones por si hay que salirse
        if not currentSymbolStrategy:  # El contrato de esta Orden ejecutada no tiene esta estrategia
            return False

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
        logging.info ('Orden ejecutada en estrategia %s. Hemos %s %d posiciones. Ahora tenemos %d', symbol, lAccion, delta_pos, currentSymbolStrategy['currentPos'])


        # Si no es Kickoff, cancelo la otra vieja que queda

        if not kickOff:
            if orderPermId == currentSymbolStrategy['UpperOrderPermId']:
                logging.info ('Orden ejecutada en estrategia %s. Cancelamos la LowerOrderId %s', symbol, currentSymbolStrategy['LowerOrderId'])
                self.RTLocalData_.orderCancelByOrderId (currentSymbolStrategy['LowerOrderId'])                 #Cancelo anterior lower limit
                currentSymbolStrategy['LowerOrderPermId'] = None
                currentSymbolStrategy['LowerOrderId'] = None
            if orderPermId == currentSymbolStrategy['LowerOrderPermId']:
                logging.info ('Orden ejecutada en estrategia %s. Cancelamos la UpperOrderId %s', symbol, currentSymbolStrategy['UpperOrderId'])
                self.RTLocalData_.orderCancelByOrderId (currentSymbolStrategy['UpperOrderId'])                    #Cancelo anterior Upper limit
                currentSymbolStrategy['UpperOrderPermId'] = None
                currentSymbolStrategy['UpperOrderId'] = None

        # Qué hacemos si la LMT de borde no ha ejecutado todas las ordenes??
        # Podemos esperar a que se finalice y dejar los bordes actuales. Pero no creo que sea buiena idea
        # Lo mejor es seguir por si nos vamos de madre poder salirnos


        logging.info ('Orden ejecutada en estrategia %s. Generamos los bordes', symbol )
        new_currentSymbolStrategy = self.strategyPentagramaCreateBorderOrders (contract, currentSymbolStrategy)

        if new_currentSymbolStrategy != None:  # El None me viene si estamos fuera de rango. 
            self.strategyPentagramaUpdate (new_currentSymbolStrategy)
        else:
            currentSymbolStrategy['timelasterror'] = datetime.datetime.now()
            self.strategyPentagramaUpdate (currentSymbolStrategy)  # dejamos el antiguo con las borders a None y nueva posicion
                                                                   # debería volver a intentarlo despues
        

    def strategyPentagramaCreateBorderOrders (self, contract, currentSymbolStrategy, ifNotExists=False):

        # IfNotExists se usa cuando quiero regenerar porque he perdido algun borde. Solo los genero si no existen
        updateUpper = True
        updateLower = True
        if ifNotExists and self.RTLocalData_.orderCheckIfExistsByOrderPermId(currentSymbolStrategy['UpperOrderPermId']):
            logging.info ('   Generando borders. No se actualiza la upper' )
            updateUpper = False
        if ifNotExists and self.RTLocalData_.orderCheckIfExistsByOrderPermId(currentSymbolStrategy['LowerOrderPermId']):
            logging.info ('   Generando borders. No se actualiza la upper' )
            updateLower = False

        symbol = currentSymbolStrategy['symbol']       
        current_prices_last = contract['currentPrices']['LAST'] 

        if current_prices_last == None:
            return None
    
        # Llevo un tracking de las posiciones de la estrategia. Solo considero las que meto yo.
        if not currentSymbolStrategy['currentPos']:
            current_pos = 0
        else:
            current_pos = currentSymbolStrategy['currentPos']

        # Sacamos las zonas de esta estrategia para este contrato
        # Detectamos en qué zona estamos, y si es la primera o ultima
        zoneFirst = False
        zoneLast = False
               
        current_zone = None
        current_zone_n = None
        for zone_n in range(len(currentSymbolStrategy['zones'])):
            if currentSymbolStrategy['zones'][zone_n]['limitDown'] < current_prices_last <= currentSymbolStrategy['zones'][zone_n]['limitUp']:
                current_zone = currentSymbolStrategy['zones'][zone_n]
                current_zone_n = zone_n
                break

        if current_prices_last > currentSymbolStrategy['zones'][zone_n]['limitUp']:
            return None # Habría que comprobar si hay posiciones y hacer salida de emergencia

        if current_prices_last < currentSymbolStrategy['zones'][zone_n]['limitDown']:
            return None # Habría que comprobar si hay posiciones y hacer salida de emergencia

        if current_zone_n == 0:
            zoneFirst = True
            logging.info ('   Estamos en la zona %d (Primera)',  current_zone_n)
        elif current_zone_n == (len(currentSymbolStrategy['zones']) - 1):
            zoneLast = True
            logging.info ('   Estamos en la zona %d (Ultima)',  current_zone_n)
        else:
            logging.info ('   Estamos en la zona %d',  current_zone_n)

        
        # Identificamos las posiciones que necesitamos para ir a la zona superior o inferior
        # Solo considero las posiciones a las que hago tracking. (current_pos) Si hay más se supone que son manuales y no las considero
        if not zoneFirst:
            pos_n_Upper = currentSymbolStrategy['zones'][current_zone_n-1]['reqPos']
        else:
            pos_n_Upper = current_pos
        if not zoneLast:
            pos_n_Lower = currentSymbolStrategy['zones'][current_zone_n+1]['reqPos']
        else:
            pos_n_Lower = current_pos

        # Ahora sacamos los precios del limite superior e inferior
        if not zoneFirst:
            prevZoneUpperLimit = currentSymbolStrategy['zones'][current_zone_n-1]['limitUp']
            price_Upper = current_zone['limitUp'] + abs(prevZoneUpperLimit - current_zone['limitUp']) * currentSymbolStrategy['OverlapMargin']
        else:
            price_Upper = current_zone['limitUp']
        if not zoneLast:
            nextZoneLowerLimit = currentSymbolStrategy['zones'][current_zone_n+1]['limitDown']
            price_Lower = current_zone['limitDown'] - abs(nextZoneLowerLimit - current_zone['limitDown']) * currentSymbolStrategy['OverlapMargin']
        else:
            price_Lower = current_zone['limitDown']
                
        # Definimos las ordenes límite de la zona actual
        secType = contract['contract'].secType
        oType = 'LMTGTC'
        if updateUpper:
            lmtPrice = price_Upper
            if zoneFirst: # La Upper sería cerrar todo
                action = 'BUY'
                qty = current_pos
            else:
                action = 'SELL'
                qty = abs(pos_n_Upper - current_pos)
            
            logging.info ("Vamos a abrir una order de limite up para %s", symbol)
            newreqUpId = self.appObj_.placeOrderBrief (symbol, secType, action, oType, lmtPrice, qty) #Orden de Upper limit
            if newreqUpId == None:
                currentSymbolStrategy['UpperOrderId'] = None
            else:
                currentSymbolStrategy['UpperOrderId'] = newreqUpId
            currentSymbolStrategy['UpperOrderPermId'] = None
        
        if updateLower:
            lmtPrice = price_Lower
            if zoneLast: # La Upper sería cerrar todo 
                action = 'SELL'
                qty = current_pos
            else:
                action = 'BUY'
                qty = abs(pos_n_Lower - current_pos)
            logging.info ("Vamos a abrir una order de limite down para %s", symbol)
            newreqDownId = self.appObj_.placeOrderBrief (symbol, secType, action, oType, lmtPrice, qty)  #Orden de Lower
            if newreqUpId == None:
                currentSymbolStrategy['LowerOrderId'] = None   # En el loop saltara que falta un leg y volverá aquí.
            else:
                currentSymbolStrategy['LowerOrderId'] = newreqDownId
            currentSymbolStrategy['LowerOrderPermId'] = None
    
        # Actualizar fichero con nuevas ordenes limite
        return currentSymbolStrategy
    
    



    

