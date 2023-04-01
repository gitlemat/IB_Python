import logging
import datetime
import strategyPentagrama
import strategyPentagramaRu


logger = logging.getLogger(__name__)
Error_orders_timer_dt = datetime.timedelta(seconds=90)

class Strategies():

    def __init__(self, RTlocalData, appObj):
        self.RTLocalData_ = RTlocalData
        self.appObj_ = appObj
        self.RTLocalData_.strategies_ = self
        
        self.strategyPentagramaObj_ = strategyPentagrama.strategyPentagrama(self.RTLocalData_)
        self.strategyPentagramaRuObj_ = strategyPentagramaRu.strategyPentagramaRu(self.RTLocalData_)


    

    # EN el loop. Esta es la maestra que mira que todos los contratos del Index tienen bien todo
    def strategyIndexCheckAll (self):
        self.strategyPentagramaObj_.strategyPentagramaLoopCheck ()
        self.strategyPentagramaRuObj_.strategyPentagramaRuLoopCheck ()

    def strategyGetStrategyBySymbol(self, symbol):
        ret = self.strategyPentagramaObj_.strategyPentagramaGetStrategyBySymbol (symbol)
        if ret is not None:
            return 'PentagramaHE'
        ret = self.strategyPentagramaRuObj_.strategyPentagramaRuGetStrategyBySymbol (symbol)
        if ret is not None:
            return 'PentagramaRu'
        return None

    def strategyGetStrategyByOrderId(self, orderId):
        ret = self.strategyPentagramaObj_.strategyPentagramaGetStrategyByOrderId (orderId)
        if ret is not None:
            return ret
        ret = self.strategyPentagramaRuObj_.strategyPentagramaRuGetStrategyByOrderId (orderId)
        if ret is not None:
            return ret
        return None
    
    # Para cuando haya que actualizar las ordenes (de orderId a PermId)
    def strategyIndexOrderUpdate (self, data):

        orderId = data['orderId']
        order = self.RTLocalData_.orderGetByOrderId(orderId) # Nos va a dar su permId que usaremos para los datos guardados        
        if not order:
            return
        gConId = order['contractId'] 
        symbol = self.RTLocalData_.contractSummaryBrief(gConId)

        self.strategyPentagramaObj_.strategyPentagramaOrderUpdated (symbol, data)  # Si defino mas ordenes, añado lineas como esta
        self.strategyPentagramaRuObj_.strategyPentagramaRuOrderUpdated (symbol, data)
    
    # Se ha ejecutado una orden y hay que ver si corresponde a alguna estrategia para temas de influx
    def strategyIndexOrderExecuted (self, data):
        if not 'executionObj' in data:
            return
        executionObj = data ['executionObj']
        orderId = executionObj.orderId
        logging.info ('Orden Ejecutada : %d', orderId)
        order = self.RTLocalData_.orderGetByOrderId(orderId) # Nos va a dar su permId que usaremos para los datos guardados        
        gConId = order['contractId'] 
        symbol = self.RTLocalData_.contractSummaryBrief(gConId)

        stratType = self.strategyGetStrategyByOrderId(orderId) 
        if stratType == 'PentagramaHE':
            self.strategyPentagramaObj_.strategyPentagramaOrderExecuted (symbol, data)

    def strategyIndexOrderCommission (self, data):
        if not 'CommissionReport' in data:
            return
        commissionReport = data ['CommissionReport']
        #self.strategyPentagramaObj_.strategyPentagramaOrderCommission (symbol, commissionReport)
