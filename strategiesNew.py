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
        gConId = order['contractId'] 
        symbol = self.RTLocalData_.contractSummaryBrief(gConId)

        toWrite = {}

        for strategy in self.stratList_:
            if strategy['symbol'] == symbol:  # Podria identificar mirando si la orderId es de esta Strategia, pero puede que lo que coincida sea permdId
                ret = strategy['classObject'].strategyOrderUpdated(data)
                if ret:
                    toWrite[strategy['type']] = True

        self.strategyWriteFile(toWrite)
    
    # Se ha ejecutado una orden y hay que ver si corresponde a alguna estrategia para temas de influx
    # Cada vez que se llega una ejecución la guardamos, y despues cuando llegan las comisiones, lo analizamos y mandamos a influx
    # Las comisiones no traen el orderId, por lo que hay que guardar las exec para enlazar la comission con la ordenId
    def strategyIndexOrderExecuted (self, data):
        if not 'executionObj' in data:
            return
        executionObj = data ['executionObj']
        exec_contract = data['contractObj']
        orderId = executionObj.orderId
        logging.info ('[Execution (%d)] Orden Ejecutada. ExecId: %s, Number/Price: %s at %s, Cumulative: %s,  Side: %s, Type: %s', orderId,executionObj.execId, executionObj.shares, executionObj.price,  executionObj.cumQty, executionObj.side, exec_contract.secType)

        toWrite = {}

        strategy_type = None
        currentSymbolStrategy = None

        # Miramos que la orden pertenezca a alguna estrategia
        for strategy in self.stratList_:
            if strategy['classObject'].strategyGetIfOrderId(orderId) == True: 
                #ret = strategy['classObject'].strategyOrderExecuted(data)
                currentSymbolStrategy = strategy['classObject']
                strategy_type = strategy['type']
                break

        if currentSymbolStrategy == None:
            return False     

        # Miramos que la estrategia esté activada (debería)
        if currentSymbolStrategy.stratEnabled_ == False:
            return False

        order = self.RTLocalData_.orderGetByOrderId(orderId) # Nos va a dar su permId que usaremos para los datos guardados

        # Si no está executed quiere decir que el Exec me ha venido antes que el Filled. Se lo mando a strategyOrderUpdated
        if order['Executed'] == False:
            data2 = {'orderId': orderId, 'contractObj': exec_contract, 'orderObj': order['order'], 'paramsDict':None }
            currentSymbolStrategy.strategyOrderUpdated (data2)  # Esto es por asegurar, por si solo llega el exec

        # Info de debug
        logging.debug ('Order Executed:')
        logging.debug ('  Symbol: %s (%s)', exec_contract.symbol, exec_contract.secType)
        logging.debug ('  ExecId: %s', executionObj.execId)
        logging.debug ('  OrderId/PermId: %s/%s', executionObj.orderId, executionObj.permId)
        logging.debug ('  Number/Price: %s at %s', executionObj.shares, executionObj.price)
        logging.debug ('  Cumulative: %s', executionObj.cumQty)
        logging.debug ('  Liquidity: %s',executionObj.lastLiquidity)
        
        # Pillamos el contrato para que Pandas y generamos el dict con los datos que ncesita Pandas
        gConId = order['contractId']
        contract = self.RTLocalData_.contractGetContractbyGconId(gConId)

        lRemaining = order['order'].totalQuantity - executionObj.cumQty

        if lRemaining > 0:
            logging.info ('[Execution (%d)] ExecId: %s. Aun no hemos cerrado todas las posciones. Vamos %d de %d', orderId,executionObj.execId, executionObj.cumQty, order['order'].totalQuantity)
            return

        numLegs = len(contract['contractReqIdLegs'])
        contract_secType = contract['contract'].secType
        exec_secType = exec_contract.secType     # Solo guardamos las de la BAG (o el que sea el que lancé)

        data_new = {}
        data_new['ExecId'] = executionObj.execId
        data_new['OrderId'] = executionObj.orderId
        data_new['PermId'] = executionObj.permId
        data_new['Quantity'] = executionObj.shares
        data_new['Cumulative'] = executionObj.cumQty
        data_new['Side'] = executionObj.side
        data_new['numLegs'] = numLegs
        data_new['contractSecType'] = contract_secType
        data_new['execSecType'] = exec_secType
        data_new['strategy_type'] = strategy_type
        data_new['lastFillPrice'] = order['params']['lastFillPrice']

        # Pandas va a guardar cada execId para cuando llegue la comission 
        currentSymbolStrategy.pandas_.dbAddExecOrder(data_new)
        

    def strategyIndexOrderCommission (self, data):
        if not 'CommissionReport' in data:
            return
        commissionReport = data ['CommissionReport']
        ExecId = data['CommissionReport'].execId

        logging.info ('[Comision (%s)] recibida', ExecId)

        execFound = False

        # Voy preguntando en cada estrategia si reconoce el comission (usando el ExecId que se guardo exed)
        for strategy in self.stratList_:
            ret = strategy['classObject'].pandas_.dbAddCommissionsOrder(commissionReport)
            if ret:
                execFound = True
        
        if not execFound:
            logging.error ('[Comision (%s)] sin ExecId reconocido', ExecId)

    def strategyUpdateZones (self, symbol, strategyType, zones, onlyNOP=False):

        toWrite = {}
        for strategy in self.stratList_:
            if strategy['symbol'] == symbol and strategy['type'] == strategyType:
                strategy['classObject'].strategyUpdateZones(zones, onlyNOP)
                toWrite[strategy['type']] = True
                self.strategyWriteFile(toWrite)



