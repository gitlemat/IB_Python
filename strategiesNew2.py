import logging
import datetime
import strategyPentagramaRuNew2
import pandas as pd


logger = logging.getLogger(__name__)

class Strategies():

    def __init__(self, RTlocalData, appObj):
        
        self.RTLocalData_ = RTlocalData
        self.appObj_ = appObj

        self.RTLocalData_.strategies_ = self

        self.stratTypes_ = {'PentagramaRu', 'Pentagrama'}

        # Como respuesta de la lectura me llega un dict con esto:
        #  {'symbol': lineSymbol, 'type': 'Pentagrama', 'classObject': classObject}

        self.stratList_ = [] 
        
        try:
            self.strategyInit()
        except:
            logging.error('Fallo cargando estrategias')

    def strategyInit(self):
        tstratList = [] 
        
        try:
            tstratList += strategyPentagramaRuNew2.strategyReadFile(self.RTLocalData_)
        except:
            logging.error ('Error cargando estrategiaRu')
            raise

        self.stratList_ = tstratList  # Si recargo, solo me las cargo si ha ido todo bien

        # Hay que asegurarse qe todos los contratos estan en la lista:
        for strategy in self.stratList_: 
            contractN = self.appObj_.contractFUTcreate(strategy['symbol'])
            gConId = self.RTLocalData_.contractAdd(contractN)
            self.RTLocalData_.contractIndirectoSet (gConId, False)

    
    def strategyGetAll (self):
        return self.stratList_

    def strategyGetAllExecs (self):
        df = pd.DataFrame()
        for strategy in self.stratList_:
            dfPart_ = strategy['classObject'].pandas_.dbGetExecsDataframeAll()
            dfPart_['Strategy'] = strategy['type'] + '/' + strategy['symbol']
            df = pd.concat([df, dfPart_])

        return df

    def strategyEnableDisable (self, symbol, strategyType, state):
        toWrite = {}
        for strategy in self.stratList_:
            if strategy['symbol'] == symbol and strategy['type'] == strategyType:
                strategy['classObject'].strategyEnableDisable(state)
                toWrite[strategy['type']] = True
                self.strategyWriteFile(toWrite)
    
    # Este es el loop que mira todas las estrategias
    def strategyIndexCheckAll (self):
        toWrite = {}
        for strategy in self.stratList_:
            ret = strategy['classObject'].strategyLoopCheck()
            if ret:
                logging.info ('[Estrategia %s (%s)]. Actualizo Fichero', strategy['type'], strategy['symbol'])
                toWrite[strategy['type']] = True

        self.strategyWriteFile(toWrite)

    def strategyIndexFix (self, data):
        # data: 
        #   stratType
        #   symbol
        #   ldata (datos para la strat)
        stratType = data['stratType']
        symbol = data['symbol']
        ldata = data['ldata']
        
        toWrite = {}
        ret = None
        for strategy in self.stratList_:
            if strategy['symbol'] == symbol and strategy['type'] == stratType:
                ret = strategy['classObject'].strategyFix(ldata)
                if ret:
                    logging.info ('[Estrategia %s (%s)]. Actualizo Fichero', strategy['type'], strategy['symbol'])
                    toWrite[strategy['type']] = True

        self.strategyWriteFile(toWrite)

    def strategyReload (self, stratType, symbol):
        for strategy in self.stratList_:
            if strategy['symbol'] == symbol and strategy['type'] == stratType:
                strategy['classObject'].strategyReloadFromFile()

    def strategyGetStrategyTypesBySymbol(self, symbol):   # Mejor concatenar si hay mas de una
        stratTypes = []
        for strategy in self.stratList_:
            if strategy['symbol'] == symbol:
                stratTypes.append(strategy['type'])
        return stratTypes

        return None

    def strategyGetStrategyBySymbolAndType(self, symbol, strategyType):   # Mejor concatenar si hay mas de una
        for strategy in self.stratList_:
            if strategy['symbol'] == symbol and strategy['type'] == strategyType:
                return strategy

        return None

    def strategyGetStrategyByOrderId(self, orderId):
        for strategy in self.stratList_:
            if strategy['classObject'].strategyGetIfOrderId(orderId):
                return {'strategy':strategy['type'], 'symbol':strategy['symbol']}
        return None

    def strategyGetStrategyObjByOrderId(self, orderId):
        for strategy in self.stratList_:
            if strategy['classObject'].strategyGetIfOrderId(orderId):
                return strategy
        return None

    def strategySubscribeOrdersInit(self):
        for strategy in self.stratList_:
            strategy['classObject'].strategySubscribeOrdersInit()
        return None

    def strategyWriteFile (self, toWrite):
            
        if 'PentagramaRu' in toWrite and toWrite['PentagramaRu'] == True:
            strategyList = []
            for strategy in self.stratList_:
                if strategy['type'] == 'PentagramaRu':
                    strategyList.append (strategy)
            strategyPentagramaRuNew2.strategyWriteFile(strategyList)
    
    # Para cuando haya que actualizar las ordenes (de orderId a PermId)
    def strategyIndexOrderUpdate (self, data):

        orderId = data['orderId']
        order = self.RTLocalData_.orderGetByOrderId(orderId) # Nos va a dar su permId que usaremos para los datos guardados        
        if not order:
            return
            
        orderPermId = order['permId']
        gConId = order['contractId'] 
        symbol = self.RTLocalData_.contractSummaryBrief(gConId)

        toWrite = {}

        ordenObj = data['orderObj']

        for strategy in self.stratList_:
            if strategy['classObject'].strategyGetIfOrderId(orderId) or strategy['classObject'].strategyGetIfOrderPermId(orderPermId):
                # Es mejor que continue para procesar cosas pendientes. Bloqueamos ordenes nuevas. Lo dejo para acrdarme de porque es mejor aí
                if strategy['classObject'].stratEnabled_ == False:   
                    pass

                bChanged = False

                # Miramos todos los orderBlocks para ver si hay cambio del orderId o permId
                if ordenObj != "":
                    for orderBlock in strategy['classObject'].orderBlocks_:
                        ret = orderBlock.orderBlockOrderIdUpdated(ordenObj)
                        if ret:
                            bChanged = True

                # Si la orden que acaba de cambiar no está asociada a la strat: se pone
                if not order['strategy']:
                    self.RTLocalData_.orderSetStrategy (orderId, strategy['classObject'])

                # Comprobamos lo que tiene que hacer el order block de la orden que ha cambiado
                if 'status' in order['params']:
                    dataBlock = {}
                    dataBlock ['orderId'] = orderId
                    dataBlock ['orderStatus'] = order['params']['status']
    
                    for orderBlock in strategy['classObject'].orderBlocks_:
                        ret = orderBlock.orderBlockOrderUpdated(dataBlock)
                        # ret:
                        #   True or False por si ha cambiado
                        #   -1 Indica que hay que parar la estrategia por salida de SL
                        if ret == -1:
                            logging.info ('###################################################')
                            logging.info ('ALARMA !!!!!!!')
                            logging.info ('Estrategia: %s [%s]', strategy['classObject'].straType_, symbol)
                            logging.info ('Nos hemos salido por SL. Caquita')
                            logging.info ('Paramos la estrategia (si no lo esta ya) porque estamos fuera de rango')
                            strategy['classObject'].stratEnabled_ = False
                            bChanged = True
                        elif ret:
                            bChanged = True

                # Por ultimo, llamamos a las strat por si tiene que hacer algo
                ret = strategy['classObject'].strategyOrderUpdated(data)
                if ret:
                    bChanged = True

                if bChanged:
                    toWrite[strategy['type']] = True

        self.strategyWriteFile(toWrite)

    def strategyUpdateZones (self, symbol, strategyType, zones, onlyNOP=False):

        toWrite = {}
        for strategy in self.stratList_:
            if strategy['symbol'] == symbol and strategy['type'] == strategyType:
                strategy['classObject'].strategyUpdateZones(zones, onlyNOP)
                toWrite[strategy['type']] = True
                self.strategyWriteFile(toWrite)



