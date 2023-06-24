import logging
import datetime
import pandasDB
from strategyClass import strategyBaseClass


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

#
# API FE
#
# strategyUpdateZones

# API Strategies
#
# strategyOrderExecuted
# strategyOrderCommission
# strategyOrderUpdated

# Implementacion 1

STRAT_File = 'strategies/HE_Mariposa_Verano.conf'


def strategyReadFile (RTlocalData):
    with open(STRAT_File) as f:
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
        datafields = {}
        datafields['symbol'] = lineSymbol
        datafields['stratEnabled'] = lineStratEnabled
        datafields['cerrarPosiciones'] = lineCerrarPosiciones
        datafields['currentPos'] = lineCurrentPos
        datafields['UpperOrderId'] = lineUpperOrderId
        datafields['UpperOrderPermId'] = lineUpperOrderPermId
        datafields['LowerOrderId'] = lineLowerOrderId
        datafields['LowerOrderPermId'] = lineLowerOrderPermId
        datafields['OverlapMargin'] = lineOverlapMargin
        datafields['zones'] = zones
        classObject = strategyPentagrama (RTlocalData, lineSymbol, datafields)
        lineFields = {'symbol': lineSymbol, 'type': 'Pentagrama', 'classObject': classObject}
        lstrategyList.append(lineFields)

    logging.info ('Estrategias Pentagrama cargadas')

    return lstrategyList

def strategyWriteFile (strategies):  
    lines = []
    header = '#Symbol        , En, UpOrdId, UpOrdPermId, LoOrdId, LoOrdPermId, CurrPos, Overlap, [reqPos, limUp, limDo, reqPos, limUp, limDo, reqPos, limUp, limDo, reqPos, limUp, limDo, reqPos, limUp, limDo]\n'
    lines.append(header)
    for strategyItem in strategies:
        line = str(strategyItem['symbol']) + ','  
        line += 'True,' if strategyItem['classObject'].stratEnabled_ == True else 'False,'
        line += 'True,' if strategyItem['classObject'].cerrarPosiciones_ == True else 'False,'
        line += ' ,' if strategyItem['classObject'].UpperOrderId_ == None else str(strategyItem['classObject'].UpperOrderId_) + ','
        line += ' ,' if strategyItem['classObject'].UpperOrderPermId_ == None else str(strategyItem['classObject'].UpperOrderPermId_) + ','
        line += ' ,' if strategyItem['classObject'].LowerOrderId_ == None else str(strategyItem['classObject'].LowerOrderId_) + ','
        line += ' ,' if strategyItem['classObject'].LowerOrderPermId_ == None else str(strategyItem['classObject'].LowerOrderPermId_) + ','
        line += ' ,' if strategyItem['classObject'].currentPos_ == None else str(int(strategyItem['classObject'].currentPos_)) + ','
        line += str(strategyItem['classObject'].OverlapMargin_) + ','
        for zone in strategyItem['classObject'].zones_:
            line += str(zone['reqPos']) + ',' + str(zone['limitUp']) + ',' + str(zone['limitDown']) + ','
        line = line [:-1] + '\n'
        lines.append(line)
    with open(STRAT_File, 'w') as f:
        for line in lines:
            f.writelines(line)

class strategyPentagrama(strategyBaseClass):
    
    def __init__(self, RTlocalData, symbol, data):
        self.stratInit (RTlocalData, symbol, data)

    def stratInit(self, RTlocalData, symbol, data):
        self.RTLocalData_ = RTlocalData

        self.symbol_ = data['symbol']
        self.stratEnabled_ = data['stratEnabled']
        self.cerrarPosiciones_ = data['cerrarPosiciones']
        self.currentPos_ = data['currentPos']
        self.UpperOrderId_ = data['UpperOrderId']
        self.UpperOrderPermId_ = data['UpperOrderPermId']
        self.LowerOrderId_ = data['LowerOrderId']
        self.LowerOrderPermId_ = data['LowerOrderPermId']
        self.OverlapMargin_ = data['OverlapMargin']
        self.zones_ = data['zones']
        self.zonesNOP_ = data['zones']
        self.lastCurrentZone_ = None
        self.lastCurrentZoneBufferPriceUp_ = None
        self.lastCurrentZoneBufferPriceDown_ = None
        self.timelasterror_ = datetime.datetime.now()
        self.pandas_ = pandasDB.dbPandasStrategy (self.symbol_, 'Pentagrama', self.RTLocalData_.influxIC_)  
        #zonesNOP sirve como No Operativa. Por si queremos hacer cambios con confirmacion
        self.ordersUpdated_ = True

    def strategySubscribeOrdersInit (self):       
        if self.UpperOrderId_ != None:
            self.RTLocalData_.orderSetStrategy (self.UpperOrderId_, 'Pentagrama')
        if self.LowerOrderId_ != None:
            self.RTLocalData_.orderSetStrategy (self.LowerOrderId_, 'Pentagrama')
        return False
    
    def strategyGetIfOrderId(self, orderId):
        if self.UpperOrderId_ == orderId or self.LowerOrderId_ == orderId:
            return True
        return False
    
    def strategyEnableDisable (self, state):
        self.stratEnabled_ = state
        return True # La strategies new tiene que actualizar fichero!!!

    def strategyCheckEnabled (self, symbol):
        # Devolver si está habilidata o no 
        return self.stratEnabled_

    def strategyLoopCheck (self): 
        
        error = 0 
        bUpdate = False

        if self.stratEnabled_ == False:
            # MISSING: habria que comprobar que no hay border orders y borrarlas.
            return False

        symbol = self.symbol_
        contract = self.RTLocalData_.contractGetBySymbol(symbol)
    
        # Miro a ver si tenemos la zona actual
        if self.lastCurrentZone_ == None or \
            self.lastCurrentZoneBufferPriceUp_ == None or \
            self.lastCurrentZoneBufferPriceDown_ == None:
            error += 10
        
        # Ahora localizar si tenemos las ordenes de arriba y abajo
        if (self.UpperOrderPermId_ == None) and (self.UpperOrderId_ == None):
            #logging.error('No tengo la Upper Order de %s', symbol)
            # Hace falta generar la Upper
            error += 100
        elif (self.UpperOrderPermId_ != None) and (not self.RTLocalData_.orderCheckIfExistsByOrderPermId(self.UpperOrderPermId_)):
            # Esto significa que la orden ha desaparecido. Esto necesita un error fuerte!!!!
            #logging.error('La Upper Order de %s (orderId: %s) ya no existe', symbol, str(currentSymbolStrategy['UpperOrderPermId']))
            error += 100
        elif self.RTLocalData_.orderGetStatusbyOrderId (self.UpperOrderId_) == 'Cancelled':
            error += 100
    
        if (self.LowerOrderPermId_ == None) and (self.LowerOrderId_ == None):
            #logging.error('No tengo la Lower Order de %s', symbol)
            error += 200
        elif (self.LowerOrderPermId_ != None) and (not self.RTLocalData_.orderCheckIfExistsByOrderPermId(self.LowerOrderPermId_)):
            # Esto significa que la orden ha desaparecido. Esto necesita un error fuerte!!!!
            #logging.error('La Lower Order de %s (orderId: %s) ya no existe', symbol, str(currentSymbolStrategy['LowerOrderPermId']))
            error += 200
        elif self.RTLocalData_.orderGetStatusbyOrderId (self.LowerOrderId_) == 'Cancelled':
            error += 200
    
        if self.currentPos_ == None:   # None es solo al principio (KO), despues puede ser 0 pero no None
            error += 1000 
        
        # Ahora arreglamos lo que sea
        # Este implica que solo nos falta la current_zone
        #logging.error ('Errores totales: %d', error)
        if error > 10:
            if (datetime.datetime.now() - self.timelasterror_) < Error_orders_timer_dt:
                return False
        if 0 < error <= 10:
            if self.UpperOrderId_ == 'KO':
                return False
            current_prices_last = contract['currentPrices']['LAST']  
            logging.info ('No tengo current zone en %s', symbol)
            if not current_prices_last:
                logging.info ('No tengo LAST price en %s', symbol)
            else:
                # Ya está el KO hecho y todo. Si falta esto, lo pillo de Pos
                current_zone_n = self.strategyGetCurrentZoneByPos()
                if current_zone_n == None:
                    logging.error ('Hay algun problema identificando la zona de %s por posiciones', symbol)
                    current_zone_n = self.strategyGetCurrentZoneByPrice(current_prices_last) 
                if current_zone_n != None:
                    price_Upper, price_Lower = self.strategyGetBorderPrices (current_zone_n)
                    self.lastCurrentZone_ = current_zone_n
                    self.lastCurrentZoneBufferPriceUp_ = price_Upper
                    self.lastCurrentZoneBufferPriceDown_ = price_Lower
                    logging.info ('Zona de %s recuperada: %d', symbol, current_zone_n)
                else:
                    logging.error ('No se ha podido recuperar la zona de %s', symbol)
                    self.timelasterror_ = datetime.datetime.now()
                bUpdate = True
    
        # Este indica que nos faltan las border
        if 99 < error < 1000:
            logging.error ('A la estrategia de %s le faltan borders. Error %d', symbol, error )
            n_new_zone = self.strategyGetCurrentZoneByPos ()
            ret = self.strategyCreateBorderOrders (contract, n_new_zone)
            if ret != None:
                bUpdate = True  # Actualizo con los datos de ordenes borde que acabo de obtener
            else:
                # deberiamos mirar que no haya posiciones, y pausar la estrategia
                logging.error ('Fallo en loopcheck: Error al general las border orders directamente')
                self.timelasterror_ = datetime.datetime.now()
            error = 0
    
        # Nos falta hacer un KO
        if error >= 1000:
            ret = self.strategyKickOff()
            if ret:
                bUpdate = True

        return bUpdate

    def strategyReloadFromFile(self):
        with open(STRAT_File) as f:
            lines = f.readlines()
        
        logging.info ('Leyendo Estrategia %s [Pentagrama] de fichero', self.symbol_)
        
        bFound = False
        for line in lines[1:]: # La primera linea es el header
            fields = line.split(',')
            lineSymbol = fields[0].strip()

            # Solo nos interesa la de self.symbol_
            if lineSymbol == self.symbol_:
                bFound = True
                break
        
        if bFound == False:
            logging.error ('No he encontrado la linea en el fichero que actualiza esta estrategia %s', self.symbol_)
            return False
            
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
    
        if len(zones) < 4:
            logging.error('Estrategia %s tiene solo %d zonas. Minimo es 4',self.symbol_, len(zones))
            lineStratEnabled = False
    
        #lineFields = {'symbol': lineSymbol, 'stratEnabled': lineStratEnabled, 'cerrarPosiciones': lineCerrarPosiciones,'currentPos': lineCurrentPos, 'lastCurrentZone': None, 'lastCurrentZoneBufferPriceUp': None, 'lastCurrentZoneBufferPriceDown': None, 'UpperOrderId': lineUpperOrderId, 'UpperOrderPermId': lineUpperOrderPermId, 'LowerOrderId': lineLowerOrderId, 'LowerOrderPermId': lineLowerOrderPermId, 'OverlapMargin': lineOverlapMargin, 'zones': zones, 'zonesNOP': zones, 'timelasterror': ahora}
        self.stratEnabled_ = lineStratEnabled
        self.cerrarPosiciones_ = lineCerrarPosiciones
        self.currentPos_ = lineCurrentPos
        self.UpperOrderId_ = lineUpperOrderId
        self.UpperOrderPermId_ = lineUpperOrderPermId
        self.LowerOrderId_ = lineLowerOrderId
        self.LowerOrderPermId_ = lineLowerOrderPermId
        self.OverlapMargin_ = lineOverlapMargin
        self.zones_ = zones
        self.zonesNOP_ = zones
        self.ordersUpdated_ = True
        
        logging.info ('Estrategias %s [Pentagrama] recargada de fichero', self.symbol_)
        
        return True

    def strategyGetCurrentZoneByPos (self):
        nPos = self.currentPos_
        current_zone_n = None
        for zone_n in range(len(self.zones_)):
            if self.zones_[zone_n]['reqPos'] == nPos:
                current_zone_n = zone_n  
        if current_zone_n != None: 
            logging.info('La estrategia %s está en zona: %d', self.symbol_, current_zone_n)
        else:
            logging.error('La estrategia %s está fuera de todas las zonas (pos: %d)', self.symbol_, nPos)
        return current_zone_n
    
    def strategyGetCurrentZoneByPrice (self, current_prices_last):
        current_zone_n = None
        for zone_n in range(len(self.zones_)):
            if self.zones_[zone_n]['limitDown'] < current_prices_last <= self.zones_[zone_n]['limitUp']:
                current_zone_n = zone_n
                break

        if current_zone_n != None:
            logging.info('La estrategia %s está en zona: %s (Last_Price: %.3f)', self.symbol_, current_zone_n, current_prices_last)
        else:
            logging.error('La estrategia %s está fuera de todas las zonas (Last_Price: %.3f)', self.symbol_, current_zone_n)
        return current_zone_n

    def strategyGetBorderPrices (self, current_zone_n):
        zoneFirst = False
        zoneLast = False
        zoneBeforeFirst = False
        zoneBeforeLast = False

        if current_zone_n == 0:
            zoneFirst = True
        if current_zone_n == 1:
            zoneBeforeFirst = True
        if current_zone_n == (len(self.zones_) - 1):
            zoneLast = True
        if current_zone_n == (len(self.zones_) - 2):
            zoneBeforeLast = True
        
        current_zone = self.zones_[current_zone_n]

        # Primero el Price Uppper
        if zoneFirst:
            price_Upper = current_zone['limitUp']
        elif zoneBeforeFirst: # Como la first está muy lejos, aplicamos un buffer como si fuese zona intermedia
            # Busco distancia entre upper y lower de esta zona, y lo uso como distancia genérica
            buffer = abs(current_zone['limitUp'] - current_zone['limitDown']) * self.OverlapMargin_
            price_Upper = current_zone['limitUp'] + buffer
        else:
            buffer = abs(self.zones_[current_zone_n-1]['limitUp'] - current_zone['limitUp']) * self.OverlapMargin_
            price_Upper = current_zone['limitUp'] + buffer

        # Despues el Price Lower
        if zoneLast:
            price_Lower = current_zone['limitDown']
        elif zoneBeforeLast:
            buffer = abs(current_zone['limitDown'] - current_zone['limitUp']) * self.OverlapMargin_
            price_Lower = current_zone['limitDown'] - buffer
        else:
            buffer = abs(self.zones_[current_zone_n+1]['limitDown'] - current_zone['limitDown']) * self.OverlapMargin_
            price_Lower = current_zone['limitDown'] - buffer

        logging.info ('Los border prices de %s son [%f,%f]', self.symbol_, price_Upper, price_Lower)

        return price_Upper, price_Lower



 
    def strategyUpdateZones (self, zones, onlyNOP=False):
        self.zonesNOP_ = zones
        if onlyNOP == False:
            self.zones_ = zones              
            if len(zones) < 4:
                logging.error('Estrategia %s tiene solo %d zonas. Minimo es 4',self.symbol_, len(zones))
                strategyItem['stratEnabled'] = False
            else: # Todo bien
                contract = self.RTLocalData_.contractGetBySymbol(self.symbol_)
                current_prices_last = contract['currentPrices']['LAST'] 
                if not current_prices_last:
                    logging.info ('No tengo LAST price en %s', self.symbol_)
                else:
                    current_zone_n = self.strategyGetCurrentZoneByPrice(current_prices_last) 
                    if current_zone_n != None:
                        price_Upper, price_Lower = self.strategyGetBorderPrices (current_zone_n)
                        self.lastCurrentZone_ = current_zone_n
                        self.lastCurrentZoneBufferPriceUp_ = price_Upper
                        self.lastCurrentZoneBufferPriceDown_ = price_Lower
                    else:
                        self.timelasterror_ = datetime.datetime.now()
            #self.strategyPentagramaUpdate (strategyItem)
            return True  # Actualizar fichero!!!!!

    def strategyKickOff (self):
        
        symbol = self.symbol_
        # No tenemos las ordenes de arriba y abajo, y quizá 
        contract = self.RTLocalData_.contractGetBySymbol(symbol)
        current_prices_last = contract['currentPrices']['LAST']  

        if not current_prices_last:
            return False

        # buscamos los datos de este contrato en concreto    

        logging.info ('Estrategia en kickoff: %s', symbol)
    
        # Como es la primera, la pillo por precio.
        current_zone_n = self.strategyGetCurrentZoneByPrice(current_prices_last)
        
        if current_zone_n == None:
            return False# Precio fuera de rango de zones

        self.lastCurrentZone_ = current_zone_n

        # Aquí hay que ordenar comprar o vender (depende de si es posiv o neg) y con un bracket. No sé hacerlo.
        needed_pos = self.zones_[current_zone_n]['reqPos']
    
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
                self.timelasterror_ = datetime.datetime.now()
                return True # Hay que actualizar
            # Marco con un flag(KO) en el fichero para que cuando llegue el evento lo reconozca y sepa que estamos en KickOff
            self.UpperOrderId_ = 'KO'
            self.LowerOrderId_ = newreqId 
            self.currentPos_ = 0
            self.ordersUpdated_ = True
        else: # Si es cero creo directamente las borders y quitamos el KO ya que no esperamos orden de KickOff
            ret = self.strategyCreateBorderOrders (contract, None)
            if ret == False:
                logging.error ('Fallo en kickoff: Error al general las border orders directamente')
                self.timelasterror_ = datetime.datetime.now()
            self.currentPos_ = 0
    
        return True

    # Al principio las border orders solo tienen el ordenId, con esto se pone el permId en cuanto llega de IB
    # Pero tambien sirve para actualizar la orderId usandp la permId

    def strategyOrderUpdated (self, data):

        if self.stratEnabled_ == False:
            return

        bChanged = False

        # Ahora miramos si hay que actualizar los orderID/permId

        ordenObj = data['orderObj']
        if ordenObj != "":
            ret = self.strategyOrderIdUpdated (ordenObj)
            if ret:
                bChanged = True

        # Y Ahora miramos si hay un cambio de estado.

        orderId = data['orderId']
        order = self.RTLocalData_.orderGetByOrderId(orderId) # Nos va a dar su permId que usaremos para los datos guardados

        if not order:
            logging.error ('Error leyendo la orderId %s', str(orderId))
            return bChanged

        if not 'status' in order['params']:
            return bChanged
        
        orderStatus = order['params']['status']   # Ya está actualizado por el Local_Daemon justo antes de llamar a estrategia

        if orderStatus == 'Filled':
            self.strategyOrderFilled (order)
            bChanged = True
        if orderStatus == 'Cancelled':
            self.strategyOrderCancelled (order)
            bChanged = True

        return bChanged


    def strategyOrderIdUpdated (self, ordenObj):
        symbol = self.symbol_
        bChanged = False
        if self.UpperOrderPermId_ == None and self.UpperOrderId_ == ordenObj.orderId:
            logging.info ('Orden actualizada en estrategia %s. Nueva UpperOrderPermId: %s', symbol, ordenObj.permId)
            self.UpperOrderPermId_ = ordenObj.permId
            bChanged = True
        elif self.LowerOrderPermId_ == None and self.LowerOrderId_ == ordenObj.orderId:
            logging.info ('Orden actualizada en estrategia %s. Nueva LowerOrderPermId: %s', symbol, ordenObj.permId)
            self.LowerOrderPermId_ = ordenObj.permId
            bChanged = True
        elif self.UpperOrderPermId_ == ordenObj.permId and self.UpperOrderId_ != ordenObj.orderId:  # Esto es por si el orderId cambia (el permId no puede cambiar)
            logging.info ('Orden actualizada en estrategia (o inicializamos) %s. Nueva UpperOrderId: %s', symbol, ordenObj.orderId)
            self.UpperOrderId_ = ordenObj.orderId
            bChanged = True
        elif self.LowerOrderPermId_ == ordenObj.permId and self.LowerOrderId_ != ordenObj.orderId:
            logging.info ('Orden actualizada en estrategia (o inicializamos)  %s. Nueva LowerOrderId: %s', symbol, ordenObj.orderId)
            self.LowerOrderId_ = ordenObj.orderId
            bChanged = True
        
        if bChanged:
            self.ordersUpdated_ = True

        return bChanged
                
    def strategyOrderFilled (self, order):
        
        # La exec trae el order_id que use para cargar el contrato asociado
        orderId = order['order'].orderId
        orderPermId = order['order'].permId    
        
        gConId = order['contractId']
        contract = self.RTLocalData_.contractGetContractbyGconId(gConId)
 
        symbol = self.symbol_
    
        kickOff = False
        if self.UpperOrderId_ == 'KO':
            kickOff = True

        if order['Executed'] == True:   # Ya la hemos evaluado
            return False

        logging.info ('Orden filled en estrategia %s. OrderId: %s', symbol, orderId)

        if kickOff and orderId != self.LowerOrderId_:
            return False

        if (not kickOff) and (orderPermId != self.LowerOrderPermId_) and (orderPermId != self.UpperOrderPermId_):
            return False # No es ninguna orden de nuestra estrategia
        
        lRemaining = int(order['params']['remaining'])
        if lRemaining > 0:
            logging.info ('     Nos faltan %d shares por ejecutar en la orden (%s)', lRemaining, orderId)
            return False  # Volverá

        lAccion = ''
        # Llevo un tracking de las posiciones de la estrategia. Solo considero las que meto yo.
        if order['order'].action == 'BUY':                  #delta_pos es el impacto de la orden que se acaba de ejecutar
            lAccion = 'comprado'
            delta_pos = order['params']['filled']
        else:
            lAccion = 'vendido'
            delta_pos = (-1) * order['params']['filled']
        self.currentPos_ += delta_pos  # La posición va a ser la que tenía más el cambio
        logging.info ('    Hemos %s %d posiciones. Ahora tenemos %d', lAccion, delta_pos, self.currentPos_)
        
        self.RTLocalData_.orderSetExecutedStatus (orderId, True)    # La marcamos como Executed

        # Si no es Kickoff, cancelo la otra vieja que queda
        bCreateBorders = False
        if not kickOff:
            bUpperPermExists = self.RTLocalData_.orderCheckIfExistsByOrderPermId(self.UpperOrderPermId_)
            bUpperPermStatus = self.RTLocalData_.orderGetStatusbyOrderPermId (self.UpperOrderPermId_)
            bUpperExists = self.RTLocalData_.orderCheckIfExistsByOrderId(self.UpperOrderId_) 
            bUpperStatus = self.RTLocalData_.orderGetStatusbyOrderId (self.UpperOrderId_)
            
            bLowerPermExists = self.RTLocalData_.orderCheckIfExistsByOrderPermId(self.LowerOrderPermId_)
            bLowerPermStatus = self.RTLocalData_.orderGetStatusbyOrderPermId (self.LowerOrderPermId_)
            bLowerExists = self.RTLocalData_.orderCheckIfExistsByOrderId(self.LowerOrderId_) 
            bLowerStatus = self.RTLocalData_.orderGetStatusbyOrderId (self.LowerOrderId_)

            if orderPermId == self.UpperOrderPermId_:
                if bLowerPermStatus == 'Filled':
                    bCreateBorders = True
                else:
                    logging.info ('    Cancelamos la LowerOrderId %s', self.LowerOrderId_)
                    self.RTLocalData_.orderCancelByOrderId (self.LowerOrderId_)         #Cancelo anterior lower limit
            if orderPermId == self.LowerOrderPermId_:
                if bUpperPermStatus == 'Filled':
                    bCreateBorders = True
                else:
                    logging.info ('    Cancelamos la UpperOrderId %s', self.UpperOrderId_)
                    self.RTLocalData_.orderCancelByOrderId (self.UpperOrderId_)         #Cancelo anterior Upper limit
        else:  # Si es kickoff no no vamos a tener una cancel order que continue el proceso
            bCreateBorders = True
        
        if bCreateBorders:
            logging.info ('    Generamos los bordes' )

            n_new_zone = self.strategyGetCurrentZoneByPos ()

            self.LowerOrderPermId_ = None
            self.LowerOrderId_ = None
            self.UpperOrderPermId_ = None
            self.UpperOrderId_ = None

            
            ret = self.strategyCreateBorderOrders (contract, n_new_zone)
    
            if ret == False:  # El None me viene si estamos fuera de rango. 
                self.timelasterror_ = datetime.datetime.now()

        
    def strategyOrderCancelled (self, order):
        
        orderId = order['order'].orderId
        orderPermId = order['order'].permId    
        
        gConId = order['contractId']
        contract = self.RTLocalData_.contractGetContractbyGconId(gConId)
 
        #symbol = self.RTLocalData_.contractSummaryBrief(gConId)
        symbol = contract['fullSymbol']
    
        kickOff = False
        if self.UpperOrderId_ == 'KO':
            kickOff = True

        logging.info ('Orden cancelada en estrategia %s. OrderId: %s', symbol, orderId)

        if kickOff and orderId != self.LowerOrderId_:
            return False

        if (not kickOff) and (orderPermId != self.LowerOrderPermId_) and (orderPermId != self.UpperOrderPermId_):
            return False # No es ninguna orden de nuestra estrategia

        if kickOff: # Empezamos de cero
            self.LowerOrderPermId_ = None
            self.LowerOrderId_ = None
            self.UpperOrderPermId_ = None
            self.UpperOrderId_ = None
            self.currentPos_ = None
            return True

        n_new_zone = self.strategyGetCurrentZoneByPos ()

        bUpperPermExists = self.RTLocalData_.orderCheckIfExistsByOrderPermId(self.UpperOrderPermId_)
        bUpperPermStatus = self.RTLocalData_.orderGetStatusbyOrderPermId (self.UpperOrderPermId_)
            
        bLowerPermExists = self.RTLocalData_.orderCheckIfExistsByOrderPermId(self.LowerOrderPermId_)
        bLowerPermStatus = self.RTLocalData_.orderGetStatusbyOrderPermId (self.LowerOrderPermId_)

        # Aqui ya sabemos que no es kickoff, y se ha cancelado una border.
        # No cancelo todas ciegamente por si se ha cancelado de alguna manera rara
        logging.info ('    Generamos los bordes' )
        if orderPermId == self.UpperOrderPermId_:
            self.LowerOrderPermId_ = None
            self.LowerOrderId_ = None
            if bLowerPermExists and bLowerPermStatus not in ['PreSubmitted', 'PendingSubmit', 'Submitted']: 
                self.UpperOrderPermId_ = None
                self.UpperOrderId_ = None

        if orderPermId == self.LowerOrderPermId_:
            self.UpperOrderPermId_ = None
            self.UpperOrderId_ = None
            if bUpperPermExists and bUpperPermStatus not in ['PreSubmitted', 'PendingSubmit', 'Submitted']:
                self.LowerOrderPermId_ = None
                self.LowerOrderId_ = None
        
        ret = self.strategyCreateBorderOrders (contract, n_new_zone)

        if ret == False:  # El None me viene si estamos fuera de rango. 
            self.timelasterror_ = datetime.datetime.now()
        
        return True  # dejamos el antiguo con las borders a None y nueva posicion
                                                                   # debería volver a intentarlo despues
    
    def strategyCreateBorderOrders (self, contract, nextZone = None):

        # IfNotExists se usa cuando quiero regenerar porque he perdido algun borde. Solo los genero si no existen
        symbol = self.symbol_ 
        logging.info ('Vamos a generar las border orders de %s', symbol )
        updateUpper = True
        updateLower = True
        bUpperPermExists = self.RTLocalData_.orderCheckIfExistsByOrderPermId(self.UpperOrderPermId_)
        bUpperPermStatus = self.RTLocalData_.orderGetStatusbyOrderPermId (self.UpperOrderPermId_)
        bUpperExists = self.RTLocalData_.orderCheckIfExistsByOrderId(self.UpperOrderId_) 
        bUpperStatus = self.RTLocalData_.orderGetStatusbyOrderId (self.UpperOrderId_)
        
        bLowerPermExists = self.RTLocalData_.orderCheckIfExistsByOrderPermId(self.LowerOrderPermId_)
        bLowerPermStatus = self.RTLocalData_.orderGetStatusbyOrderPermId (self.LowerOrderPermId_)
        bLowerExists = self.RTLocalData_.orderCheckIfExistsByOrderId(self.LowerOrderId_) 
        bLowerStatus = self.RTLocalData_.orderGetStatusbyOrderId (self.LowerOrderId_)
        
        if bUpperPermExists and bUpperPermStatus != 'Cancelled' and bUpperPermStatus != 'Filled':
            logging.info ('   Generando borders. No se actualiza la upper' )
            updateUpper = False
        elif bUpperExists and bUpperStatus != 'Cancelled' and bUpperStatus != 'Cancelled' and self.UpperOrderPermId_ == None:
            #La orderId la tengo pero no me ha llegado la permId
            logging.info ('   Generando borders. No se actualiza la upper. Tenemos la odrderId y permId no ha llegado' )
            updateUpper = False
        else:
            logging.info ('   Generando borders. La upper se va a regenerar' )

        if bLowerPermExists and bLowerPermStatus != 'Cancelled' and bLowerPermStatus != 'Filled':
            logging.info ('   Generando borders. No se actualiza la Lower' )
            updateLower = False
        elif bLowerExists and bLowerStatus != 'Cancelled' and bLowerStatus != 'Filled' and self.LowerOrderPermId_ == None:
            logging.info ('   Generando borders. No se actualiza la Lower. Tenemos la odrderId y permId no ha llegado' )
            updateLower = False
        else:
            logging.info ('   Generando borders. La Lower se va a regenerar' )

        # Llevo un tracking de las posiciones de la estrategia. Solo considero las que meto yo.
        if not self.currentPos_:
            current_pos = 0     # Viene de KO
        else:
            current_pos = self.currentPos_

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
                return False
            current_zone_n = self.strategyGetCurrentZoneByPrice(current_prices_last)

        if current_zone_n == None:
            logging.error ('Al no tener zona no podemos crear las border')
            return False

        self.lastCurrentZone_ = current_zone_n

        if current_zone_n == 0:
            zoneFirst = True
            logging.info ('   Estamos en la zona %d (Primera)',  current_zone_n)
        elif current_zone_n == (len(self.zones_) - 1):
            zoneLast = True
            logging.info ('   Estamos en la zona %d (Ultima)',  current_zone_n)
        else:
            logging.info ('   Estamos en la zona %d',  current_zone_n)

        price_Upper, price_Lower = self.strategyGetBorderPrices (current_zone_n)

        self.lastCurrentZoneBufferPriceUp_ = price_Upper
        self.lastCurrentZoneBufferPriceDown_ = price_Lower

        # Identificamos las posiciones que necesitamos para ir a la zona superior o inferior
        # Solo considero las posiciones a las que hago tracking. (current_pos) Si hay más se supone que son manuales y no las considero
        if not zoneFirst:
            pos_n_Upper = self.zones_[current_zone_n-1]['reqPos'] - current_pos
        else:
            pos_n_Upper = current_pos * (-1)

        if not zoneLast:
            pos_n_Lower = self.zones_[current_zone_n+1]['reqPos'] - current_pos
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
                self.UpperOrderId_ = None
            else:
                self.UpperOrderId_ = newreqUpId
            self.UpperOrderPermId_ = None
        
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
                self.LowerOrderId_ = None   # En el loop saltara que falta un leg y volverá aquí.
            else:
                self.LowerOrderId_ = newreqDownId
            self.LowerOrderPermId_ = None
    
        # Actualizar fichero con nuevas ordenes limite
        self.ordersUpdated_ = True
        return True