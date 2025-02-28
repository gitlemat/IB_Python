import logging
import datetime
import pandasDB
import strategyOrderBlock
from strategyClass2 import strategyBaseClass
import utils



logger = logging.getLogger(__name__)

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
# - ParentFilled+EP: La parent se ha ejecutado, y la partent tiene error. Se da cuando despues de ejecutar la parent, desaparece la child. Todo hecho?
# - ParentFilled+EC: La parent se ha ejecutado, y error en childs
# - +EC            : Parent NO ejecutada y error en childs


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
        logging.debug ('############## %s', line)

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

    if bError:
        raise Exception("Error cargando estrategiaRu")
        return

    logging.info ('Estrategias PentagramaRu cargadas')

    return lstrategyList

def strategyWriteFile (strategies):  
    lines = []
    header = '# Symbol        , En, CurrPos, \n'
    lines.append(header)
    header = '# B/S,Price,qty,PrecioSL,PrecioTP,OrdId,OrdPermId,OrdIdSL,OrdPermIdSL,OrdIdTP,OrdPermIdTP,ToBeDelete,FilledState\n'
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
            ret = strategyOrderBlock.bracketOrderParseToFile(zone['orderBlock'])
            if ret['result'] == True:
                lines.append(ret['line'])
            else:
                logging.info('Borrada esta linea del fichero: %s', ret['line'])
        line = '%\n'
        lines.append(line)
    with open(STRAT_File, 'w') as f:
        for line in lines:
            f.writelines(line)

def strategyPentagramaRuAddToFile (data):
    logging.info('Añadiendo estrat a RU: %s', data)
    symbol = data['symbol']
    nBuys = data['nBuys']
    nSells = data['nSells']
    interSpace = data['interSpace']
    gain = data['gain']
    start = data['start']
    qty_row = str(data['qty_row'])
    sl_buy = str(data['sl_buy'])
    sl_sell = str(data['sl_sell'])
    row = ''
    #HEZ3-2HEG4+HEJ4,False,False,0
    row = symbol+',False,False,0\n'
    value = start
    for n in range(nSells):
        valueStr = str(round(value,4))
        tp = str(round(value - gain,4))
        row += 'S,' + valueStr + ',' + qty_row + ',' + sl_sell + ',' + tp + ',,,,,,,,None\n'
        value -= interSpace
    for n in range(nBuys):
        valueStr = str(round(value,4))
        tp = str(round(value + gain,4))
        row += 'B,' + valueStr + ',' + qty_row + ',' + sl_buy + ',' + tp + ',,,,,,,,None\n'
        value -= interSpace
    row += '%\n'

    with open(STRAT_File, 'a') as f:
        for line in row:
            f.writelines(line)

def strategyPentagramaDeleteFromFile (data):
    logging.info('Borrando estrat a RU: %s', data)
    if 'symbol' not in data:
        logging.error ('No hay symbol en data. No se puede borrar')
        raise Exception ('Error borrando estrategia de fichero')
    symbol = data['symbol']

    with open(STRAT_File) as f:
        lines = f.readlines()
        
    lines_to_write = ""

    bWrite = True
    for line in lines:
        if line == '':
            continue
        if line[0] not in ['B', 'S', '#', '%']:
            fields = line.split(',')
            lineSymbol = fields[0].strip()
            if lineSymbol == symbol:
                bWrite = False
            else:
                bWrite = True
        if bWrite:
            lines_to_write += line

    with open(STRAT_File, 'w') as f:
        for line in lines_to_write:
            f.writelines(line)

    logging.info ('Estrategia PentagramaRU %s Borrada')

    return 


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
        #   self.orderBlocks_ = []
        #   self.timelasterror_ = datetime.datetime.now()

        self.straType_ = 'PentagramaRu'
        self.pandas_ = pandasDB.dbPandasStrategy (self.symbol_, 'PentagramaRu', self.RTLocalData_.influxIC_)
        self.zones_ = [] # En realidad es innecesario. Podemos considerar zone=orderBlock

        regen = not self.cerrarPos_

        # Da la casualidad que cada zona corresponde a un BracketOrder. Es innecesario mantener zones_, pero por si mas adelante hace falta
        for zoneItem in data['zones']:
            logging.debug('Zone Nueva:')
            logging.debug('\n%s', zoneItem)
            orderBlock = strategyOrderBlock.bracketOrderClass(zoneItem, self.symbol_, self.straType_, regen, self.RTLocalData_)
            zone = {'orderBlock': orderBlock}
            self.zones_.append(zone)
            # En todas las strats tiene que haber una lista con todos los orderBlocks
            self.orderBlocks_.append(orderBlock)

    def strategySetCerrarPos(self, value):
        if value not in [True, False]:
            return False
        regen = not value   # Si quiero cerrar pocision (True) entonces regen = False
        for block in self.orderBlocks_:
            block.oderBlockRegenChange(regen)
        self.cerrarPos_ = value

        if value == True:
            self.strategyCancelarOrdenesNuevasPosiciones()
        return True

    def strategyLoopCheck (self): 
        # Nada fuera de lo normal. Hacemos solo lo standard de la clase base
        ret = super().strategyLoopCheck()

        new_pos = self.strategyCalcularPosiciones()

        if self.currentPos_ != new_pos:
            self.currentPos_ = new_pos
            if ret == None:
                ret = True

        # Ahora tenemos que revisar si algun orderblock está en TBDready. Esos se borrar (junto con sus zonas)
        for zoneItem in self.zones_:
            if zoneItem['orderBlock'].BracketOrderTBD_ == 'TBDready':
                self.strategyDeleteZone(zoneItem)
                if ret == None:
                    ret = True
        return ret

    def strategyFix (self, data):
        #data:
        #    orderId -> con esto identifico la zona
        # asumimos que si el order es parent, se recrea todo, si es child, solo la OCA
        if 'orderId' in data:
            lorderId = data['orderId']
        elif 'orderIntId' in data:
            lorderIntId = data['orderIntId']
        else:
            logging.error('StrategyFix sin orderId. %s', data)
            return False

        ret = False

        if 'orderId' in data:
            lorderId = data['orderId']

            for zoneItem in self.zones_:
                if zoneItem['orderBlock'].orderBlockGetIfOrderId(lorderId):
                    if lorderId == zoneItem['orderBlock'].orderId_:
                        fixType = 'ALL'
                    else:
                        fixType = 'OCA'
                    data = {'fixType': fixType}
                    logging.info ('[Estrategia PentagramaRu (%s)] Vamos a hacer un fix de orderId: %s, y fixType: %s', self.symbol_, lorderId , fixType)
                    ret = zoneItem['orderBlock'].orderBlockOrderFix(data)
                    if ret != None:
                        self.ordersUpdated_ = True
                    break
        elif 'orderIntId' in data:
            lorderIntId = data['orderIntId']
            for zoneItem in self.zones_:
                if zoneItem['orderBlock'].orderBlockGetIfOrderIntId(lorderIntId):
                    data = {'fixType': 'ALL'}
                    logging.info ('[Estrategia PentagramaRu (%s)] Vamos a hacer un fix de orderIntId: %s, y fixType: ALL', self.symbol_, lorderIntId)
                    ret = zoneItem['orderBlock'].orderBlockOrderFix(data)
                    if ret != None:
                        self.ordersUpdated_ = True
                    break

        return ret

    def strategyAssumeError (self, data):
        ret = False

        lorderId = data['orderId']

        for zoneItem in self.zones_:
            if zoneItem['orderBlock'].orderBlockGetIfOrderId(lorderId):
                data['orderStatus'] = 'Filled'
                ret = zoneItem['orderBlock'].orderBlockOrderUpdated(data)
                if ret != None:
                    self.ordersUpdated_ = True
                break

        return ret

    def strategyGetExecPnL (self):
        return self.pandas_.dbGetExecPnL()

    def strategyGetExecPnLUnrealized (self):
        ExecData = self.pandas_.dbGetExecPnL()
        lotes_contrato = utils.getLotesContratoBySymbol (self.symbol_)
        count = ExecData['count']
        avgPrice = ExecData['avgPrice'] * lotes_contrato
        tPnL = ExecData['PnL']

        contrato = self.RTLocalData_.contractGetBySymbol(self.symbol_)
        priceLast = 0
        if contrato['currentPrices']['LAST'] != None:
            priceLast = contrato['currentPrices']['LAST'] * lotes_contrato

        comprado = float(avgPrice) * float(self.currentPos_)
        vendido_potencial = float(priceLast) * float(self.currentPos_)

        unreal = float(self.currentPos_) * (float(priceLast) - float(avgPrice))
        logging.debug ('Pos: %s', self.currentPos_)
        logging.debug ('avgPrice: %s', avgPrice)
        logging.debug ('priceLast: %s', priceLast)

        return unreal


    def strategyOrderUpdated (self, data):

        new_pos = self.strategyCalcularPosiciones()

        zero_crossing = False
        bChanged = False

        if self.currentPos_ != new_pos:
            if new_pos == 0 or (new_pos * self.currentPos_ < 0):
                zero_crossing = True
                logging.info ('[Estrategia PentagramaRu (%s)] Hemos pasado por Cero', self.symbol_)
            if self.cerrarPos_ and zero_crossing:
                logging.info ('')
                logging.info ('[Estrategia PentagramaRu (%s)] Hemos pasado por Cero y vamos a cerrar todo por mandato', self.symbol_)
                self.stratEnabled_ = False
                self.strategyCancelarTodasOrdenes()
            self.currentPos_ = new_pos
            bChanged = True

        return bChanged

    def strategyCancelarTodasOrdenes(self):
        for block in self.orderBlocks_:
            block.orderBlockCancelOrders()

    def strategyCancelarOrdenesNuevasPosiciones(self):
        for block in self.orderBlocks_:
            block.orderBlockCancelParentOrder()
        
    def strategyCalcularPosiciones (self):
        pos = 0
        for zone in self.zones_:
            # Cada zone solo tiene 1 orderBlock:
            orderBlock = zone['orderBlock']
            pos += orderBlock.orderBlockPosiciones()
        return pos

    def strategyGetBuildParams (self):
        nBuys = 0
        nSells = 0
        interSpace = None
        gain = 0
        first = None
        qty_row = 0
        sl_buy = 0
        sl_sell = 0

        prev = 0
        for zone in self.zones_:
            orderBlock = zone['orderBlock']
            if orderBlock.BracketOrderTBD_ in ['TBD', 'TBDready']:
                continue
            if orderBlock.B_S_ == 'B':
                sl_buy = orderBlock.PrecioSL_
                gain = orderBlock.PrecioTP_ - orderBlock.Price_
                nBuys += 1
            else:
                sl_sell = orderBlock.PrecioSL_
                gain = orderBlock.Price_ - orderBlock.PrecioTP_
                nSells += 1
            if not first or orderBlock.Price_ > first:
                first = orderBlock.Price_
            qty_row = orderBlock.Qty_
            interSpace = abs(orderBlock.Price_ - prev)
            prev = orderBlock.Price_

        data = {}
        data['nBuys'] = nBuys
        data['nSells'] = nSells
        data['interSpace'] = round(interSpace,3)
        data['gain'] = round(gain,3)
        data['start'] = round(first,3)
        data['qty_row'] = qty_row 
        data['sl_buy'] = round(sl_buy,3)
        data['sl_sell'] = round(sl_sell,3)

        return (data)

    def strategyGetOrdersDataFromParams(self, data):
        # Devuelve una lista con las ordenes que tenemos en la strat 
        # Y añadimos las que generamos con los param de data
        # cada orden no es una class, sino un dict
        # Esto lo hacemos para poder mostrarlo en pantalla en un review.

        logging.info('Calculando ordenes de estrat a RU: %s', data)
        lista_orderblocks = []
        lista_orderblocks_new = []

        for orderBlock in self.orderBlocks_:
            orden = {}
            orden['B_S'] = orderBlock.B_S_
            orden['Price'] = orderBlock.Price_
            orden['PrecioTP'] = orderBlock.PrecioTP_
            orden['PrecioSL'] = orderBlock.PrecioSL_
            orden['Qty'] = orderBlock.Qty_
            orden['TBD'] = 'TBD' 
            orden['Status'] = orderBlock.BracketOrderFilledState_
            lista_orderblocks.append(orden)

        logging.debug ('Lista de orderblocks existentes: %s', lista_orderblocks)

        if data == None:
            return lista_orderblocks

        symbol = data['symbol']
        nBuys = data['nBuys']
        nSells = data['nSells']
        interSpace = data['interSpace']
        gain = data['gain']
        start = data['start']
        qty_row = data['qty_row']
        sl_buy = data['sl_buy']
        sl_sell = data['sl_sell']
        
        value = start
        for n in range(nSells):
            value = round(value,4)
            tp = round(value - gain,4)
            orden = {}
            orden['B_S'] = 'S'
            orden['Price'] = value
            orden['PrecioTP'] = tp
            orden['PrecioSL'] = sl_sell
            orden['Qty'] = qty_row
            orden['TBD'] = 'New' 
            orden['Status'] = ""
            lista_orderblocks_new.append(orden)
            value -= interSpace
        for n in range(nBuys):
            value = round(value,4)
            tp = round(value + gain,4)
            orden = {}
            orden['B_S'] = 'B'
            orden['Price'] = value
            orden['PrecioTP'] = tp
            orden['PrecioSL'] = sl_buy
            orden['Qty'] = qty_row
            orden['TBD'] = 'New' 
            orden['Status'] = ""
            lista_orderblocks_new.append(orden)
            value -= interSpace

        logging.debug ('Lista de orderblocks nuevas: %s', lista_orderblocks_new)

        lista_orderblocks_new_filtered = []

        for order_new in lista_orderblocks_new:
            bIgual_out = False
            for order in lista_orderblocks:
                bIgual = True
                if order['B_S'] != order_new['B_S']:
                    bIgual = False
                if order['Price'] != order_new['Price']:
                    bIgual = False
                if order['PrecioTP'] != order_new['PrecioTP']:
                    bIgual = False
                if order['PrecioSL'] != order_new['PrecioSL']:
                    bIgual = False
                if order['Qty'] != order_new['Qty']:
                    bIgual = False
                if bIgual:
                    order['TBD'] = '' 
                    #lista_orderblocks_new.remove(order_new)
                    bIgual_out = True
            if not bIgual_out:
                lista_orderblocks_new_filtered.append(order_new)

        lista_orderblocks += lista_orderblocks_new_filtered
        lista_orderblocks = sorted(lista_orderblocks, key=lambda d: d['Price'], reverse=True)

        logging.debug ('Lista de orderblocks final: %s', lista_orderblocks)

        return lista_orderblocks

    def strategyActualizaZonesDesdeGUI (self, data):
        error = False
        alert_msg = ""
        alert_color = 'danger'

        try:
            # Ojo que esta no es lista de class, sino lista de dicts 
            lista_orderblocks = self.strategyGetOrdersDataFromParams(data)
        except:
            logging.error ("Exception occurred añadiendo estrategia", exc_info=True)
            alert_msg = "Error adquiriendo las zonas desde los params"
            ret = {'alert_msg': alert_msg, 'alert_color': alert_color}
            return ret

        # Aqui tenemos una lista de order_blocks a generar y borrar, pero todo lo puede hacer la clase orderbracket.
        # Aquí solo hay que actualizar el fichero y config
        #   - Creamos zona nueva si es nuevo
        #   - Lo marcamos para borrar si ya no lo quiero

        for order_block_data in lista_orderblocks:
            if order_block_data['TBD'] == 'New':
                try:
                    self.strategyAddZone(order_block_data)
                except:
                    alert_msg = "Error añadiendo zona en estrategia"
                    logging.error('Error añadiendo zona en estrategia.', exc_info=True)
                    error = True
            else:
                try:
                    ret = self.strategyUpdateTBD(order_block_data)
                except:
                    alert_msg = "Error cambiando TBD en estrategia"
                    logging.error('Error cambiando TBD en estrategia.', exc_info=True)
                    error = True
                else:
                    if ret == False:
                        alert_msg = "Error cambiando TBD en estrategia"
                        logging.error('Error cambiando TBD en estrategia. Zona no encontrada')
                        error = True

        if not error:
            toWrite = {'PentagramaRu': True}
            try:
                # Esto no es elegante, pero es comodo
                self.RTLocalData_.strategies_.strategyWriteFile(toWrite)
            except:
                alert_msg = "Error escribiendo estrategia en fichero"
                logging.error('Error escribiendo estrategia.', exc_info=True)
            else:
                alert_color = 'success'
                alert_msg = "Zonas añadidas y/o actualizadas correctamente. Recarga"
                logging.info ('Commit de Strat Updata. Todo correcto')
        
        ret = {'alert_msg': alert_msg, 'alert_color': alert_color}
        return ret

    def strategyAddZone(self, data):

        #data['B_S']
        #data['Price']
        #data['Qty'] 
        #data['PrecioSL']
        #data['PrecioTP']
        
        # Opcionales:
        #data['OrderId'] 
        #data['OrderPermId']
        #data['OrderIdSL'] 
        #data['OrderPermIdSL']
        #data['OrderIdTP']
        #data['OrderPermIdTP'] 
        #data['BracketOrderTBD']
        #data['BracketOrderFilledState']

        logging.info("[Estrategia %s (%s)]. Añadiendo Zona", self.straType_, self.symbol_)

        if 'B_S' not in data:
            logging.error("     No tenemos B_S. Salimos")
            return None
        if 'Price' not in data:
            logging.error("     No tenemos Price. Salimos")
            return None
        if 'Qty' not in data:
            logging.error("     No tenemos Qty. Salimos")
            return None
        if 'PrecioSL' not in data:
            logging.error("     No tenemos PrecioSL. Salimos")
            return None
        if 'PrecioTP' not in data:
            logging.error("     No tenemos PrecioTP. Salimos")
            return None

        logging.info("     B_S: %s", data['B_S'])
        logging.info("     Price: %s", data['Price'])
        logging.info("     Qty: %s", data['Qty'])
        logging.info("     PrecioTP: %s", data['PrecioTP'])
        logging.info("     PrecioSL: %s", data['PrecioSL'])

        regen = not self.cerrarPos_
        orderBlock = strategyOrderBlock.bracketOrderClass(data, self.symbol_, self.straType_, regen, self.RTLocalData_)
        zone = {'orderBlock': orderBlock}
        self.zones_.append(zone)
        self.zones_ = sorted(self.zones_, key=lambda d: d['orderBlock'].Price_, reverse=True)
        # En todas las strats tiene que haber una lista con todos los orderBlocks
        self.orderBlocks_.append(orderBlock)
        self.orderBlocks_ = sorted(self.orderBlocks_, key=lambda d: d.Price_, reverse=True)

        logging.info("     Parace que se ha añadido correctamente")

        return True

    def strategyDeleteZone(self, zona):
        # Hay que hacerlo
        logging.info("[Estrategia %s (%s)]. Borramos Zona:", self.straType_, self.symbol_)
        logging.info("     B_S: %s", zona['orderBlock'].B_S_)
        logging.info("     Price: %s", zona['orderBlock'].Price_)
        logging.info("     Qty: %s", zona['orderBlock'].Qty_)
        logging.info("     PrecioTP: %s", zona['orderBlock'].PrecioTP_)
        logging.info("     PrecioSL: %s", zona['orderBlock'].PrecioSL_)
        self.orderBlocks_.remove(zona['orderBlock'])
        self.zones_.remove(zona)
    
    def strategyUpdateTBD (self, order_block_data):

        for order_block in self.orderBlocks_:
            if order_block.B_S_ != order_block_data['B_S']:
                continue
            if order_block.Price_ != order_block_data['Price']:
                continue
            if order_block.PrecioTP_ != order_block_data['PrecioTP']:
                continue
            if order_block.PrecioSL_ != order_block_data['PrecioSL']:
                continue
            if order_block.Qty_ != order_block_data['Qty']:
                continue
            # En este punto debería ser el bueno

            logging.info("[Estrategia %s (%s)]. Actualizamos TDB en Zona:", self.straType_, self.symbol_)
            logging.info("     B_S: %s", order_block_data['B_S'])
            logging.info("     Price: %s", order_block_data['Price'])
            logging.info("     Qty: %s", order_block_data['Qty'])
            logging.info("     PrecioTP: %s", order_block_data['PrecioTP'])
            logging.info("     PrecioSL: %s", order_block_data['PrecioSL'])
            logging.info("     Nuevo TDB: %s", order_block_data['TBD'])

            order_block.BracketOrderTBD_ = order_block_data['TBD']

            return True

        return False

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
                        regen = not lineStratCerrar
                        self.zones_ = []
                        self.orderBlocks_ = []
                        self.stratEnabled_ = lineStratEnabled
                        self.cerrarPos_ = lineStratCerrar
                        self.currentPos_ = lineCurrentPos
                        self.ordersUpdated_ = True
                        for zoneItem in zones:
                            orderBlock = strategyOrderBlock.bracketOrderClass(zoneItem, self.symbol_, self.straType_, regen, self.RTLocalData_)
                            zone = {'orderBlock': orderBlock}
                            self.zones_.append(zone)
                            # En todas las strats tiene que haber una lista con todos los orderBlocks
                            self.orderBlocks_.append(orderBlock)
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

    def strategyExecAddManual(self, data):
        self.pandas_.dbAddCommissionsOrderFill(data)

    
