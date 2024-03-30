import datetime

class strategyBaseClass():

    def __init__(self, RTlocalData, symbol, data):
        # To override
        self.RTLocalData_ = RTlocalData

        self.symbol_ = symbol
        self.stratEnabled_ = data['stratEnabled']
        self.cerrarPos_ = data['cerrarPos']
        self.currentPos_ = data['currentPos']
        self.ordersUpdated_ = data['ordersUpdated']
        
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

    def strategyGetIfOrderIntId(self, orderIntId):
        for orderBlock in self.orderBlocks_:
            ret = orderBlock.orderBlockGetIfOrderIntId(orderIntId)
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

    def strategySetCerrarPos(self, value):
        return None

    def strategyLoopCheck (self): 

        if self.stratEnabled_ == False:
            return False

        bStrategyUpdated = False

        for orderBlock in self.orderBlocks_:
            ret = orderBlock.orderBlockLoopCheck()
            if ret == True:
                bStrategyUpdated = True
                self.ordersUpdated_ = True
            if ret == -1:
                ## Esto es cuando una bracket o OCA ha sido ejecutada entera, y no rehecha. Probablente no hace falta
                bStrategyUpdated = True
                self.ordersUpdated_ = True
            if ret == -2:
                # Esto es cuando hay que borrar el orderBlock
                bStrategyUpdated = True
                self.ordersUpdated_ = True

        return bStrategyUpdated

    def strategyFix (self, data):
        return None

    def strategyAssumeError (self, data):
        return None

    def strategyGetExecPnL (self):
        return None

    def strategySubscribeOrdersInit (self): 
        # To override
        return None

    def strategyReloadFromFile (self): 
        # To override
        return None

    def strategyOrderUpdated (self, data = None):
        # To override
        return None

    def strategyCalcularPosiciones (self):
        return None

    def strategyGetBuildParams(self):
        return None

    def strategyGetOrdersDataFromParams (self, data):
        return None

    def strategyActualizaZonesDesdeGUI (self, data):
        return None
    
    def strategyUpdateTBD (self, order_block_data):
        return None

    def strategyExecAddManual(self, data):
        return None
        