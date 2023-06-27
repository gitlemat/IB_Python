import logging
import datetime
import strategyPentagramaNew
import strategyPentagramaRuNew


logger = logging.getLogger(__name__)
Error_orders_timer_dt = datetime.timedelta(seconds=90)

class Strategies():

    def __init__(self, RTlocalData, appObj):
        
        self.RTLocalData_ = RTlocalData
        self.appObj_ = appObj

        self.RTLocalData_.strategies_ = self

        # Como respuesta de la lectura me llega un dict con esto:
        #  {'symbol': lineSymbol, 'type': 'Pentagrama', 'classObject': classObject}

        self.stratList_ = [] 
        self.stratList_ += strategyPentagramaNew.strategyReadFile(self.RTLocalData_)
        self.stratList_ += strategyPentagramaRuNew.strategyReadFile(self.RTLocalData_)

        # Hay que asegurarse qe todos los contratos estan en la lista:
        for strategy in self.stratList_: 
            contractN = self.appObj_.contractFUTcreate(strategy['symbol'])
            self.RTLocalData_.contractAdd(contractN)

        self.stratTypes_ = {'PentagramaRu', 'Pentagrama'}

    def strategyGetAll (self):
        return self.stratList_

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
            
            strategyPentagramaRuNew.strategyWriteFile(strategyList)
        if 'Pentagrama' in toWrite and toWrite['Pentagrama'] == True:
            strategyList = []
            for strategy in self.stratList_:
                if strategy['type'] == 'Pentagrama':
                    strategyList.append (strategy)
            strategyPentagramaNew.strategyWriteFile(strategyList)
    
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

        for strategy in self.stratList_:
            if strategy['classObject'].strategyGetIfOrderId(orderId) or strategy['classObject'].strategyGetIfOrderPermId(orderPermId):
            #if strategy['symbol'] == symbol:  # Podria identificar mirando si la orderId es de esta Strategia, pero puede que lo que coincida sea permdId
                ret = strategy['classObject'].strategyOrderUpdated(data)
                if ret:
                    toWrite[strategy['type']] = True

        self.strategyWriteFile(toWrite)

    def strategyUpdateZones (self, symbol, strategyType, zones, onlyNOP=False):

        toWrite = {}
        for strategy in self.stratList_:
            if strategy['symbol'] == symbol and strategy['type'] == strategyType:
                strategy['classObject'].strategyUpdateZones(zones, onlyNOP)
                toWrite[strategy['type']] = True
                self.strategyWriteFile(toWrite)



