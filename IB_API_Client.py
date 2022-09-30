from ibapi.wrapper import *
from ibapi.client import *
from ibapi.contract import *
from ibapi.order import *
from ibapi.order_condition import Create, OrderCondition
from ibapi.utils import longMaxString
from ibapi.utils import iswrapper
from ibapi import utils
from ibapi.account_summary_tags import *

import time
import queue
import logging
import globales

logger = logging.getLogger(__name__)


class IBI_App(EWrapper, EClient):
    #Intializes our main classes 
    def __init__(self, ipaddress, portid, clientid, RTlocalData):
        #EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        
        Order.__setattr__ = utils.setattr_log
        Contract.__setattr__ = utils.setattr_log

        self.accSumTags = AccountSummaryTags()
        
        self.contract_details = {} #Contract details will be stored here using reqId as a dictionary key
        self.contract_details_end_flag = {}
        
        self.RTLocalData_ = RTlocalData
        self.wsServerInt_ = None
        self.nextorderId = None
        
        self.initConnected_ = False
        self.initOrders_ = False
        self.initPositions_ = False
        self.initAccount_ = False
        self.initReady_ = False

        self.semaforo_requestingOrders = False
        self.semaforo_requestingPositions = False
        self.semaforo_requestingAccount = False

        self.reqIds_ = {}

        self.accountToPrint = False
        
        self.RTLocalData_.appObj_ = self
        #globales.RTLocalData_.appObj_ = self

        self.CallbacksQueue_ = queue.Queue()
        
        #Starts listening for errors 

        #def connect_app(self, ipaddress, portid, clientid):
        #Connects to the server with the ipaddress, portid, and clientId specified in the program execution area
        self.connect(ipaddress, portid, clientid)
        '''
        #Initializes the threading
        thread = threading.Thread(target = self.run)
        thread.start()
        setattr(self, "_thread", thread)
        '''

    def reqIdNew(self):
        i = 0
        while i in self.reqIds_:
            i += 1
        self.reqIds_[i] = True
        return (i)

    def reqIdDelete(self, reqId):
        try:
            del self.reqIds_[reqId]
        except:
            pass
        
    @iswrapper
    def error(self, id, errorCode, errorString, advancedOrderRejectJson=""):
        #super().error(id, errorCode, errorString, advancedOrderRejectJson)
        ## Overrides the native method EWrapper
        if errorCode == 202:
            errormessage = "[202] Order Cancelled." 
        elif errorCode == 2104:
            errormessage = "[2104] Market data farm connection is OK."
        elif errorCode == 2106:
            errormessage = "[2106] A historical data farm is connected"
        elif errorCode == 2158:
            errormessage = "[2158] Sec-def data farm connection is OK" 
        elif errorCode == 1102:
            errormessage = "[1102] %s" % (errorString)
            self.initConnected_ = True
            self.initOrders_ = False
            self.initPositions_ = False
            self.initAccount_ = False
            self.initReady_ = False
        else:
            errormessage = "[%d] %s" % (errorCode, errorString)

        logging.error (errormessage)       
        
        
    def init_time(self):
        time_queue = queue.Queue()
        self.my_time_queue = time_queue
        return time_queue

    @iswrapper
    def currentTime(self, server_time):
        ## Overriden method EWrapper
        self.my_time_queue.put(server_time)
        
    def server_clock(self):
    
        logging.info ("Asking server for Unix time")     
    
        # Creates a queue to store the time
        time_storage = self.init_time()
    
        # Sets up a request for unix time from the Eclient
        self.reqCurrentTime()
        
        #Specifies a max wait time if there is no connection
        max_wait_time = 10
        
        try:
            requested_time = time_storage.get(timeout = max_wait_time)
        except queue.Empty:
            logging.error ("The queue was empty or max time reached")
            requested_time = None
        
        return requested_time

    @iswrapper
    def tickPrice(self, reqId, tickType, price, attrib):
        ## Overriden method EWrapper
        #print('The current ask price (',tickType,') for reqid', reqId, 'is: ', price)
        data = {'reqId': reqId, 'tickType': tickType, 'price': price, 'attrib':attrib }
        queueEntry = {'type':'tick', 'data': data}
        self.CallbacksQueue_.put(queueEntry)
        #self.RTLocalData_.tickUpdatePrice (reqId, tickType, price)

    @iswrapper
    def tickSize(self, reqId: TickerId, tickType: TickType, size: Decimal):
        #super().tickSize(reqId, tickType, size)
        data = {'reqId': reqId, 'tickType': tickType, 'size': size}
        queueEntry = {'type':'tick', 'data': data}
        self.CallbacksQueue_.put(queueEntry)
        
    
    @iswrapper
    def tickSnapshotEnd (self, tickerId):
        self.reqIdDelete(tickerId)
        
    @iswrapper
    def orderStatus(self, orderId, status, filled, remaining, avgFullPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        ## Overriden method EWrapper
        #print('orderStatus - orderid:', orderId, 'status:', status, 'filled', filled, 'remaining', remaining, 'lastFillPrice', lastFillPrice)
        #print ('orderStatus')
        paramsDict = {}
        paramsDict['status'] = status
        paramsDict['filled'] = filled
        paramsDict['remaining'] = remaining
        paramsDict['lastFillPrice'] = lastFillPrice
        paramsDict['avgFullPrice'] = avgFullPrice
        paramsDict['permId'] = permId
        paramsDict['parentId'] = parentId
        paramsDict['clientId'] = clientId
        paramsDict['whyHeld'] = whyHeld
        paramsDict['mktCapPrice'] = mktCapPrice

        data = {'orderId': orderId, 'contractObj': "", 'orderObj': "", 'paramsDict':paramsDict }
        queueEntry = {'type':'order', 'data': data}
        self.CallbacksQueue_.put(queueEntry)
    

    @iswrapper    
    def openOrder(self, orderId, contract, order, orderState):
        ## Overriden method EWrapper
        #print ('openOrder')
        #print('openOrder id:', orderId, contract.symbol, contract.secType, '@', contract.exchange, ':', order.action, order.orderType, order.totalQuantity, orderState.status) 
        paramsDict = {}
        paramsDict['orderState'] = orderState

        data = {'orderId': orderId, 'contractObj': contract, 'orderObj': order, 'paramsDict':paramsDict }
        queueEntry = {'type':'order', 'data': data}
        self.CallbacksQueue_.put(queueEntry)

    @iswrapper    
    def openOrderEnd(self):
        super().openOrderEnd()
        self.initOrders_ = True
        self.semaforo_requestingOrders = False
        logging.info ("[Orden] - Todas Leidas")

    @iswrapper    
    def execDetails(self, reqId, contract, execution):
        ## Overriden method EWrapper
        # Aqui hay que mandar a una funcion de strategy que busque en strategyTracker y lo mande al correcto (async?).
        # Un execution queue
        queueEntry = {'type':'execution', 'data': execution}
        self.CallbacksQueue_.put(queueEntry)
        print ('Order Executed (reqId: ', reqId, ')')
        print ('  Symbol:', contract.symbol,' (', contract.secType, ')')
        print ('  ExecId:', execution.execId)
        print ('  OrderId/PermId:', execution.orderId, '/', execution.permId)
        print ('  Number/Price:', execution.shares, 'at', execution.price)
        print ('  Liquidity:',execution.lastLiquidity)
   
    @iswrapper
    def execDetailsEnd(self, reqId: int):
        super().execDetailsEnd(reqId)
        logging.info ("ExecDetailsEnd. ReqId: %d", reqId)

    @iswrapper 
    def commissionReport(self, commissionReport: CommissionReport):
        super().commissionReport(commissionReport)
        print("CommissionReport.", commissionReport)

    @iswrapper
    def position(self, account: str, contract: Contract, position: Decimal, avgCost: float):
        #account:    the account holding the position.
        #contract:   the position's Contract
        #position:   the number of positions held. 
        #avgCost:    the average cost of the position.

        super().position(account, contract, position, avgCost)
        #print ('position input:', contract)     
        data = {'contract': contract, 'position': position, 'avgCost':avgCost }
        queueEntry = {'type':'position', 'data': data}
        self.CallbacksQueue_.put(queueEntry)
    
    @iswrapper          
    def positionEnd(self):
        super().positionEnd()
        self.initPositions_ = True
        self.semaforo_requestingPositions = False
        logging.info ("[Posicion] - Todas Leidas")

    
    @iswrapper
    def nextValidId(self, orderId: int):
        ## Overriden method EWrapper
        super().nextValidId(orderId)
        self.nextorderId = orderId
        #print('The next valid order id is: ', self.nextorderId)
    
    @iswrapper    
    def contractDetails(self, reqId: int, contractDetails):
        ## Overriden method EWrapper
        #print ('Recibido')
        self.contract_details[reqId] = contractDetails
    
    @iswrapper    
    def contractDetailsEnd(self, reqId: int):
        ## Overriden method EWrapper
        self.contract_details_end_flag[reqId] = True
        self.reqIdDelete (reqId)
        
    @iswrapper    
    def accountSummary(self, reqId:int, account:str, tag:str, value:str, currency:str):
        ## Overriden method EWrapper
        #print("Acct Summary. ReqId:" , reqId , "Acct:", account, 
        #    "Tag: ", tag, "Value:", value, "Currency:", currency)
        data = {'reqId': reqId, 'account': account, 'tag':tag, 'value':value}
        queueEntry = {'type':'account', 'data': data}
        self.CallbacksQueue_.put(queueEntry)
                 
    @iswrapper
    def accountSummaryEnd(self, reqId:int):
        ## Overriden method EWrapper
        logging.info ("AccountSummaryEnd. ReqId: %d", reqId)
        self.initAccount_ = True
        self.semaforo_requestingAccount = False
        self.accountToPrint = True

    @iswrapper  
    def reqPositions (self):
        if self.semaforo_requestingPositions:
            return False
        else:
            self.semaforo_requestingPositions = True
            super().reqPositions ()
        return True

    @iswrapper    
    def reqAllOpenOrders (self):
        if self.semaforo_requestingOrders:
            return False
        else:
            self.semaforo_requestingOrders = True
            super().reqAllOpenOrders ()
        return True

    @iswrapper    
    def reqAccountSummary (self, reqId, group, tags):
        if self.semaforo_requestingAccount:
            return False
        else:
            self.semaforo_requestingAccount = True
            super().reqAccountSummary(reqId, group, tags)
        return True
        
    def get_contract_details(self, contract):
        reqId = self.reqIdNew()
        self.contract_details[reqId] = None
        self.contract_details_end_flag[reqId] = False
        resp = None
        self.reqContractDetails(reqId, contract)
        #Error checking loop - breaks from loop once contract details are obtained
        
        for err_check in range(50):
            #if not self.contract_details[reqId]:
            if not self.contract_details_end_flag[reqId]:
                time.sleep(0.1)
            else:
                resp = self.contract_details[reqId]
                del self.contract_details[reqId]  # QUito el contrato de la lista de respuestas
                break
        #Raise if error checking loop count maxed out (contract details not obtained)
        if err_check == 49:
            #print ('error')
            raise Exception('error getting contract details')
        '''
        while not self.contract_details[reqId]: #or not self.contract_details_end_flag[reqId]:
            time.sleep(1)
            print ('esperando')
        '''
        
        #Return contract details otherwise
        return resp
        
    #Function to create a Future Spread in GLOBEX by symbol 
    def letter2Month (self, letter):
        letterDict = {}
        letterDict['F'] = '01'
        letterDict['G'] = '02'
        letterDict['H'] = '03'
        letterDict['J'] = '04'
        letterDict['K'] = '05'
        letterDict['M'] = '06'
        letterDict['N'] = '07'
        letterDict['Q'] = '08'
        letterDict['U'] = '09'
        letterDict['V'] = '10'
        letterDict['X'] = '11'
        letterDict['Z'] = '12'
        if letter in letterDict:
            return letterDict[letter]
        else:
            return None
        
    def code2date (self, code): #Z2 -> 202212
        
        if len(code) != 2:
            return None
        
        month = self.letter2Month (code[-2])
        if not month:
            return None
        year = '202' + code[-1]
        date = year + month
        return (date)

    def contractCode2list (self, contractCode):
        contractList = []
        if contractCode[0] != '+' and contractCode[0] != '-':
            contractCode = '+' + contractCode
        contractCode = contractCode.replace('-',',-')
        contractCode = contractCode.replace('+',',+')
        if contractCode[0] == ',':   # Va a pasar siempre
            contractCode = contractCode[1:]
        codesList = contractCode.split(',')
        
        for code in codesList:
            cont = {}
            if code[0] == '-':
                cont['action'] = 'SELL'
            else:
                cont['action'] = 'BUY'
            code = code[1:]
            if code[0].isnumeric():
                cont['ratio'] = int(code[0])
                code = code [1:]
            else:
                cont['ratio'] = 1
            cont ['code'] = code
            contractList.append(cont)
        return contractList
        
    def contractSTKcreate (self, stkCode):
        
        contract1 = Contract()
        contract1.symbol = stkCode
        contract1.secType = 'STK'
        contract1.currency = 'USD'
        contract1.exchange = "SMART"
        
        return contract1
        
    def contractSimpleFUTcreate (self, futCode):
        symbol = futCode[:-2] # Pillo todo menos ultimas 2 chars
        code1 = futCode[-2:] # Pillo ultimas 2 chars
        date1 = self.code2date (code1)

        if not date1:
            return None
        
        contract1 = Contract()
        contract1.symbol = symbol
        contract1.secType = 'FUT'
        contract1.currency = 'USD'
        contract1.exchange = "GLOBEX"
        contract1.lastTradeDateOrContractMonth = date1
        
        return contract1

    def contractFUTcreate (self, spreadCode):
        # El codigo de contrato/spread/butterfly se convierte a lista de dict que tiene codigo y action
        contractcodeList = self.contractCode2list(spreadCode)

        if len (contractcodeList) < 1:
            return None

        if len (contractcodeList) == 1:   # No es ni spread ni butterfly
            return self.contractSimpleFUTcreate (contractcodeList[0]['code'])

        contract = Contract()
        contract.secType = 'BAG'
        contract.currency = 'USD'
        contract.exchange = "GLOBEX"
        contract.comboLegs = []

        tLocalSymbol = ''
        prevSymbol = ''
        nIter = 0
        different = False

        # Por cada Dict de la lista, tenemos el codigo del contrato y action. por cada uno creamos un contratoN para el Leg

        for contratoDict in contractcodeList:
            contractN = self.contractSimpleFUTcreate (contratoDict['code'])
            if not contractN:
                return None
            try:
                contractN = self.get_contract_details(contractN).contract
            except:
                logging.error ("Error al recibir detalles")
                return None
            self.RTLocalData_.contractAdd(contractN)

            if contractN.symbol != prevSymbol and nIter > 0:
                different = True
            prevSymbol = contractN.symbol
            tLocalSymbol += '.' + contractN.localSymbol # lo vamos preparando por si acaso
            leg1 = ComboLeg()
            leg1.conId = contractN.conId
            leg1.ratio = contratoDict['ratio']
            leg1.exchange = "GLOBEX"
            leg1.action = contratoDict['action']
            contract.comboLegs.append(leg1)

            nIter += 1
        
        if different == True:     # Segun https://interactivebrokers.github.io/tws-api/spread_contracts.html
            contract.symbol = tLocalSymbol[1:]   # el primero es un '.'
        else:
            contract.symbol = prevSymbol

        #self.RTLocalData_.contractUpdate(contract)   No lo mando porque aun no tengo el conID. Cuando IB me de el printado de la orden se añlade

        return contract 

    #Create order object
    def orderBuyMKTcreate(self, Qty):
        return self.orderCreate ('BUY', 'MKT', 0, Qty)
         
    def orderCreate(self, action, oType, lmtPrice, Qty):
        order = Order()
        order.action = action
        order.totalQuantity = Qty
        order.orderType = oType
        if oType == 'LMT':
            order.lmtPrice = lmtPrice
        
        return order  
        
    def placeOrderBrief (self, contract_symbol, secType, action, oType, lmtPrice, qty):
        if secType != 'FUT' and secType != 'STK':
            return False
        try:
            example_order = self.orderCreate (action, oType, lmtPrice, qty)
        except:
            return False

        if secType == 'FUT':
            try:
                example_contract = self.contractFUTcreate(contract_symbol)
            except:
                return False
        elif secType == 'STK':
            try:
                example_contract = self.contractSTKcreate(contract_symbol)
            except:
                return False

        try:
            self.placeOrder (example_contract, example_order)
        except:
            return False
        else:
            return True

    @iswrapper    
    def placeOrder (self, contract:Contract, order:Order):
        super().placeOrder (self.nextorderId, contract, order)
        self.nextorderId += 1
        return (self.nextorderId - 1)

    def cancelOrderByOrderId (self, orderId):
        if not self.RTLocalData_.orderCheckIfExistsByOrderId (orderId):
            return False
        super().cancelOrder (orderId, '')
        return True

    def cancelOrderAll (self):
        super().reqGlobalCancel()
        
    #####################################
    # Market requests
    
    def reqMktDataGen (self, contract):
        reqId = self.reqIdNew()
        super().reqMktData(reqId, contract, '', False, False, [])
        return reqId

    def cancelMktDataGen (self, reqId):
        super().cancelMktData(reqId)
        self.reqIdDelete(self, reqId)   # Aqué o hay callback?

          
#BID_SIZE 0
#BID 1
#ASK 2
#ASK_SIZE 3
#LAST 4
#LAST_SIZE 5
#HIGH 6
#LOW 7
#VOLUME 8
#CLOSE 9
#BID_OPTION_COMPUTATION 10
#ASK_OPTION_COMPUTATION 11
#LAST_OPTION_COMPUTATION 12
#MODEL_OPTION 13
#OPEN 14
#LOW_13_WEEK 15
#HIGH_13_WEEK 16
#LOW_26_WEEK 17
#HIGH_26_WEEK 18
#LOW_52_WEEK 19
#HIGH_52_WEEK 20
#AVG_VOLUME 21
#OPEN_INTEREST 22
#OPTION_HISTORICAL_VOL 23
#OPTION_IMPLIED_VOL 24
#OPTION_BID_EXCH 25
#OPTION_ASK_EXCH 26
#OPTION_CALL_OPEN_INTEREST 27
#OPTION_PUT_OPEN_INTEREST 28
#OPTION_CALL_VOLUME 29
#OPTION_PUT_VOLUME 30
#INDEX_FUTURE_PREMIUM 31
#BID_EXCH 32
#ASK_EXCH 33
#AUCTION_VOLUME 34
#AUCTION_PRICE 35
#AUCTION_IMBALANCE 36
#MARK_PRICE 37
#BID_EFP_COMPUTATION 38
#ASK_EFP_COMPUTATION 39
#LAST_EFP_COMPUTATION 40
#OPEN_EFP_COMPUTATION 41
#HIGH_EFP_COMPUTATION 42
#LOW_EFP_COMPUTATION 43
#CLOSE_EFP_COMPUTATION 44
#LAST_TIMESTAMP 45
#SHORTABLE 46
#FUNDAMENTAL_RATIOS 47
#RT_VOLUME 48
#HALTED 49
#BID_YIELD 50
#ASK_YIELD 51
#LAST_YIELD 52
#CUST_OPTION_COMPUTATION 53
#TRADE_COUNT 54
#TRADE_RATE 55
#VOLUME_RATE 56
#LAST_RTH_TRADE 57
#RT_HISTORICAL_VOL 58
#IB_DIVIDENDS 59
#BOND_FACTOR_MULTIPLIER 60
#REGULATORY_IMBALANCE 61
#NEWS_TICK 62
#SHORT_TERM_VOLUME_3_MIN 63
#SHORT_TERM_VOLUME_5_MIN 64
#SHORT_TERM_VOLUME_10_MIN 65
#DELAYED_BID 66
#DELAYED_ASK 67
#DELAYED_LAST 68
#DELAYED_BID_SIZE 69
#DELAYED_ASK_SIZE 70
#DELAYED_LAST_SIZE 71
#DELAYED_HIGH 72
#DELAYED_LOW 73
#DELAYED_VOLUME 74
#DELAYED_CLOSE 75
#DELAYED_OPEN 76
#RT_TRD_VOLUME 77
#CREDITMAN_MARK_PRICE 78
#CREDITMAN_SLOW_MARK_PRICE 79
#DELAYED_BID_OPTION 80
#DELAYED_ASK_OPTION 81
#DELAYED_LAST_OPTION 82
#DELAYED_MODEL_OPTION 83
#LAST_EXCH 84
#LAST_REG_TIME 85
#FUTURES_OPEN_INTEREST 86
#AVG_OPT_VOLUME 87
#DELAYED_LAST_TIMESTAMP 88
#SHORTABLE_SHARES 89
#DELAYED_HALTED 90
        
    