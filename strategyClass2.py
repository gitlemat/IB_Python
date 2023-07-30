class strategyBaseClass():

    def __init__(self, RTlocalData, symbol, data):
        # To override
        self.RTLocalData_ = RTlocalData

        self.symbol_ = symbol
        self.stratEnabled_ = data['stratEnabled']
        self.cerrarPos_ = data['cerrarPos']
        self.currentPos_ = data['currentPos']
        self.ordersUpdated_ = data['ordersUpdated']
        self.pandas_ = pandasDB.dbPandasStrategy (self.symbol_, 'PentagramaRu', self.RTLocalData_.influxIC_)  
        
        self.orderBlocks_ = []
        self.timelasterror_ = datetime.datetime.now()
        return None
    
    def strategySubscribeOrdersInit (self): 
        for orderBlock in self.orderBlocks_:
            orderBlock.orderBlockSubscribeOrdersInit()
        return None

    def strategyGetIfOrderId(self, orderId):
        for orderBlock in self.orderBlocks_:
            ret = orderBlock.orderBlockGetIfOrderId(orderId)
            if ret:
                return True
        return False
    
    def strategyGetIfOrderPermId(self, orderPermId):
        for orderBlock in self.orderBlocks_:
            ret = orderBlock.orderBlockGetIfOrderPermId(orderPermId)
            if ret:
                return True
        return False

    def strategyEnableDisable (self, state):
        self.stratEnabled_ = state
        return True # La strategies new tiene que actualizar fichero!!!

    def strategyCheckEnabled (self):
        # Devolver si está habilidata o no 
        return self.stratEnabled_

    def strategyGetAll(self):
        # To override 
        return None

    def strategyGetContractList(self):
        # To override 
        return None

    def strategyLoopCheck (self): 

        if self.stratEnabled_ == False:
            return False

        bStrategyUpdated = False

        for orderBlock in self.orderBlocks_:
            ret = orderBlock.orderBlockLoopCheck()
            if ret:
                bStrategyUpdated = True

        return bStrategyUpdated

    def strategySubscribeOrdersInit (self): 
        # To override
        return None

    def strategyReloadFromFile (self): 
        # To override
        return None

    def strategyOrderUpdated (self, data = None):
        # To override
        return None

    def strategyOrderIdUpdated (self, ordenObj):
        # To override
        return None

    def strategyOrderExecuted (self = None, data = None):
        #To override
        return None

    def strategyOrderCommission (symbol = None, commissionReport = None):
        #To override
        return None
        