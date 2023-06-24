class strategyBaseClass():

    def __init__(self, RTlocalData = None):
        # To override
        return None

    def strategyGetAll(self):
        # To override 
        return None

    def strategyGetContractList(self):
        # To override 
        return None
    
    def strategyGetIfOrderId (self, orderId = None):
        # To override
        return None

    def strategyEnableDisable (self, symbol = None, state = None):
        # To override
        return None

    def strategyCheckEnabled (self, symbol = None):
        # Devolver si está habilidata o no 
        # To override
        return None

    def strategyLoopCheck (self): 
        # To override
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

    def strategyOrderIdUpdated (self, ordenObj):
        # To override
        return None

    def strategyOrderExecuted (self = None, data = None):
        #To override
        return None

    def strategyOrderCommission (symbol = None, commissionReport = None):
        #To override
        return None

