from typing_extensions import Self
from ibapi.contract import *
from ibapi.order import *
import strategies
import pandasDB
import logging
import datetime

logger = logging.getLogger(__name__)



class DataLocalRT():
    # accountData_:
    #    accountData_: Dict con todos los tag/value que recibimos de IB
    #    toPrint: Pues eso

    # positionList_:
    #    gConId: gConId
    #    pos_n: Numero de posiciones
    #    avgCost: Coste medio?
    #    toPrint: Algo ha cambiado y hay que imprimir
    #
    # contractList_:
    #    gConId: conID + leg_conIDs...
    #    contract: contrackObj de Ib
    #    dbPandas: puntero a la dbPandas
    #    fullLegData: Si tenemos los contratos de cada leg (solo si es BAG). 
    #    contractReqIdLegs: Lista de dicts: [{'conId': , 'reqId': None, 'ratio': , 'action':, 'lsymbol':  },...]
    #    currentPrices: Precios actuales ({'BUY': 10, 'SELL': 10.2, 'LAST': 10.1})
    #    hasContractSymbols: Si ya tengo los HEJ3 para seguir los ticks. Necesito quer fulllegdata= True para poder pedirlos y tener esto a True.
    #
    # orderList_:
    #    permId: permanentId de la orden en IB
    #    contractId: gConId
    #    order: orderObj de IB
    #    params: Dict de params que se reciben como paramateros 
    #    to_print: Algo ha cambiado y hay que imprimir
    # 
    # tickPrices_:
    #    Key: reqId ['12'] ---> {12: {'BID': 10, 'ASK': 10.1, 'LAST': 10.1, 'HIGH': 11, 'LOW': 9, 'OPEN':10.5, 'CLOSE': 10.2}}
    
    def __init__(self):
        self.verboseBrief = False
        self.appObj_ = None
        self.wsServerInt_ = None
        self.strategies_ = None
        #self.strategies_ = strategies.Strategies(self)

        self.accountData_ = {}
        self.orderList_ = []  # includes orders and contracts (hay que sacar los contracts a puntero externo, y los usan las posiciones)
        self.positionList_ = []  # INcluyen enlace an contracts
        self.contractList_ = []  # Directamente lista de contracts

        self.tickPrices_ = {}    # Key: reqId ['12'] ---> {12: {'price': 10, 'symbol': 'AAPL'}}

        self.contractInconplete_ = False

    ########################################
    # Executions

    # Deberíamos tener un Pandas+CSV que guarde todas las execs.
    # Si se pierde la conexsión habría que pedir todas y comparar

    def executionAnalisys (self, execObj):
        #Podemos hacer más cosas, de momento solo informamos a las estrategias
        self.strategies_.strategyIndexOrderExecuted(execObj)


        
    ########################################
    # Account

    def accountTagUpdate (self, data):

        reqId = data['reqId']
        account = data['account']
        tag = data['tag']
        value = data['value']

        dictLocal = {}
        dictLocal[tag] = value
        self.accountData_.update (dictLocal)

    def accountSummary (self):
        summaryStr = ''
        for tag in self.accountData_:
            summaryStr += str(tag) + ": " + str(self.accountData_[tag]) + '\n'
        return summaryStr

    ########################################
    # Positions


    def positionAdd (self, gConId, nPosition, avgCost):
        
        posicion = {}
        posicion['gConId'] = gConId
        posicion['pos_n'] = nPosition
        posicion['avgCost'] = avgCost
        
        self.positionList_.append(posicion)

        posicion['toPrint'] = False   # Porque lo voy a imprimir justo en la siguiente linea
        str_o = self.positionSummary (posicion)
        logging.info (str_o)
        self.wsServerInt_.print_string(str_o)
        
        return (True)
        
    def positionUpdate (self, data):
        contractObj = data['contract']
        nPosition = data['position']
        avgCost = data['avgCost']
        result = True
        exists = False

        if not contractObj == "":
            #print ('Actualizo cont')
            self.contractAdd (contractObj)

        gConId = self.contractGetGconId(contractObj)

        for posicion in self.positionList_: 
            if posicion['gConId'] == gConId:
                exists = True
                posicion['pos_n'] = nPosition
                posicion['avgCost'] = avgCost
                #posicion['toPrint'] = True
                str_o = self.positionSummary (posicion)
                logging.info (str_o)
                self.wsServerInt_.print_string(str_o)
                break
                
        if not exists:
            result = self.positionAdd (gConId, nPosition, avgCost)
            
                        
        return (result)

    def positionDeleteAll (self):
        for posicion in self.positionList_:
            self.positionList_.remove(posicion)
        self.positionList_ = []

    def positionGetByGconId(self, gConId):
        for posicion in self.positionList_:
            if posicion['gConId'] == gConId:
                return posicion
        return None
  
    def positionSummaryAllFull (self):
        summaryStr = ''
        for posicion in self.positionList_:
            summaryStr += self.positionSummaryFull (posicion)

        return summaryStr

    def positionSummaryAllBrief (self):
        summaryStr = ''
        for posicion in self.positionList_:
            summaryStr += self.positionSummaryBrief (posicion)

        return summaryStr

    def positionSummaryAllUpdated (self):
        summaryStr = ''
        
        for posicion in self.positionList_:
            if posicion['toPrint'] == True:
                summaryStr += self.positionSummary (posicion)

        return summaryStr
        
    def positionSummary (self, posicion):        
        if self.verboseBrief == True:
            return (self.positionSummaryBrief (posicion))
        else:
            return (self.positionSummaryFull (posicion))

        
    def positionSummaryFull (self, posicion):
        summaryStr = ''

        summaryStr  = '--------------------------------------\n'
        summaryStr += 'Posicion detalles\n'
        summaryStr += '     Posicion:\n'
        summaryStr += '         nPos:' + decimalMaxString(posicion['pos_n']) + '\n'
        summaryStr += '         Avg Cost:' + floatMaxString(posicion['avgCost']) + '\n'
        
        summaryStr += '         ' + self.contractSummaryPricesOnly(posicion['gConId']) + '\n'

        summaryStr += self.contractSummaryFull(posicion['gConId'])

        posicion['toPrint'] = False
        #self.positionSetSymbolsIfNeeded (posicion)
      
        return summaryStr
        
    def positionSummaryBrief (self, posicion):
        summaryStr = ''
        
        summaryStr = '[Posicion] - ' + self.contractSummaryBrief(posicion['gConId'])
        summaryStr += ', Qty: ' +  decimalMaxString(posicion['pos_n']) + ', AvgCost: ' + floatMaxString(posicion['avgCost'])

        summaryStr += ', ' + self.contractSummaryPricesOnly(posicion['gConId'])

        posicion['toPrint'] = False  
        #self.positionSetSymbolsIfNeeded (posicion)  
        
        return summaryStr

    ########################################
    # tickPrice
    #   Key: reqId ['12'] ---> {12: {'BID': 10, 'ASK': 10.1, 'LAST': 10.1, 'HIGH': 11, 'LOW': 9, 'OPEN':10.5, 'CLOSE': 10.2}}
        
    def tickUpdatePrice (self, data):
        reqId = data['reqId']
        tickType = data['tickType']
        price = None
        if 'price' in data:
            price = data['price']
            if price == -100:  # Indica que no está disponible
                return
        size = None
        if 'size' in data:
            size = data['size']

        prices = {}
        if reqId in self.tickPrices_:
            prices = self.tickPrices_[reqId]
        
        if price != None:
            if tickType == 1 or tickType == 66:
                prices['BID'] = price
            if tickType == 2 or tickType == 67:
                prices['ASK'] = price  
            if tickType == 4 or tickType == 68:
                prices['LAST'] = price
            if tickType == 6 or tickType == 72:
                prices['HIGH'] = price
            if tickType == 7 or tickType == 73:
                prices['LOW'] = price
            if tickType == 14 or tickType == 76:
                prices['OPEN'] = price
            if tickType == 9 or tickType == 75:
                prices['CLOSE'] = price
        if size != None:
            if tickType == 0 or tickType == 69:
                prices['BID_SIZE'] = size
            if tickType == 3 or tickType == 70:
                prices['ASK_SIZE'] = size  
            if tickType == 5 or tickType == 71:
                prices['LAST_SIZE'] = size
            if tickType == 8 or tickType == 74:
                prices['VOLUME'] = size
        
        self.tickPrices_[reqId] = prices

        self.contractUpdateTicks(reqId)
      

        

    ########################################
    # contracts
       
    def contractAdd (self, contractObj):        
        if contractObj == "" or contractObj == None:
            return

        gConId = self.contractGetGconId(contractObj)
        
        for contract in self.contractList_:     
        #for contrato in self.contractList_:
            if contract['gConId'] == gConId:
                if contract['contract'].conId == 0:
                    contract['contract'].conId = contractObj.conId
                return

        contrato = {}
        contrato['gConId'] = gConId
        contrato['contract'] = contractObj
        if contractObj.secType == "BAG":
            contrato['fullLegData'] = False
        else:
            contrato['fullLegData'] = True
        contrato['dbPandas'] = None # se inicisaliza cuando tenganos los ContractSymbols (si es BAG)
        contrato['contractReqIdLegs'] = []
        contrato['currentPrices'] = {}
        contrato['currentPrices']['BUY'] = None
        contrato['currentPrices']['SELL'] = None
        contrato['currentPrices']['LAST'] = None
        contrato['currentPrices']['BUY_SIZE'] = None
        contrato['currentPrices']['SELL_SIZE'] = None
        contrato['currentPrices']['LAST_SIZE'] = None
        contrato['hasContractSymbols'] = False
                        
        self.contractList_.append(contrato)
        
        
        return True

    def contratoReturnListAll(self):
        return self.contractList_

    def contractCheckStatus (self):
        missing = False
        for contrato in self.contractList_:
            if self.contractCheckIfIncompleteSingle(contrato):    # Si no tiene los legs, upstream lo tiene que arreglar
                missing = True
            elif contrato['hasContractSymbols']:                  # Si tiene los symbols, asegurar que estan subscritos a tick
                self.contractSubscribeIfNeeded(contrato)  
            else:                                                 # Si no tiene symbols, se buscan
                self.contractSetSymbolsIfNeeded(contrato)
        self.contractInconplete_ = missing            
        return missing

    # Los legs tienen que completarse y se hace así:
    #   1.- Al hacer la orden pedimos y añadimos los contracts de los legs
    #   3.- Esto del checkIfIncompete y contractReqDetailsAllMissing se necesita para completar los legs
    #       En el loop se checkea si falta alguno (checkIfIncompete)
    #       Y se llama a contractReqDetailsAllMissing si hay que completar
    #        

    def contractReqDetailsAllMissing (self):
        if self.contractInconplete_ == False:
            return
        for contrato in self.contractList_:
            if contrato['fullLegData'] == False:
                for leg in contrato['contract'].comboLegs:          # Podria leer el fullLegData del contract, pero mejor asi
                    if self.contractCheckIfExists(leg.conId) == False:
                        contrato1 = Contract()
                        contrato1.conId = leg.conId
                        contrato1.symbol = contrato['contract'].symbol
                        contrato1.secType = 'FUT'   # las spreads considero solo FUTs
                        contrato1.currency = contrato['contract'].currency
                        contrato1.exchange = contrato['contract'].exchange
                        try:
                            contrato1 = self.appObj_.get_contract_details(contrato1).contract   # Como tengo el conId, este me devuelve todo con la fecha
                        except:
                            logging.error ("Error al recibir detalles")
                        else:
                            self.contractAdd(contrato1)

    def contractCheckIfIncompleteGlobal (self):
        missing = False
        for contrato in self.contractList_:
            if self.contractCheckIfIncompleteSingle(contrato):
                missing = True
        self.contractInconplete_ = missing
        return missing

    def contractCheckIfIncompleteSingle (self, contrato):
        missing = False
        if contrato['contract'].secType == 'BAG':
            contrato['fullLegData'] = True
            for leg in contrato['contract'].comboLegs:          # Podria leer el fullLegData del contract, pero mejor asi
                if self.contractCheckIfExists(leg.conId) == False:   # con un leg el conId = gConId
                    contrato['fullLegData'] = False
                    missing = True
        self.contractInconplete_ = missing
        return missing
        
    def contractLoadFixedWatchlist (self):

        file1 = open('strategies/fixedContracts.conf', 'r')
        Lines = file1.readlines()
  
        for line in Lines:
            contractN = self.appObj_.contractFUTcreate(line.rstrip())
            self.contractAdd(contractN)

    def contractUnsubscribeAll (self):
        for contrato in self.contractList_:
            for contractReqIdLeg in contrato['contractReqIdLegs']:
                contractReqIdLeg['reqId'] = None
        for reqId in self.tickPrices_:
            self.appObj_.cancelMktDataGen (reqId)
        self.tickPrices_ = {}

    def contractSubscribeIfNeeded (self, contrato):
        for contractReqIdLeg in contrato['contractReqIdLegs']:
            contractReqIdLeg['reqId'] = self.contractSubscribeTickPrice (contractReqIdLeg)

    def contractSetSymbolsIfNeeded(self, contrato):
        contrato['contractReqIdLegs'] = self.contractGetSymbolsIfFullLegsDataByGconId(contrato['gConId'])
        # contrato['contractReqIdLegs'] --> [{'conId': , 'reqId': None, 'ratio': , 'action': , 'lSymbol': },...]
        if len(contrato['contractReqIdLegs']) > 0:
            contrato['hasContractSymbols'] = True
            lSymbol = self.contractSummaryBrief (contrato['gConId'])   
            contrato['dbPandas'] = pandasDB.dbPandas (lSymbol)           # No se puede hasta que no tenga todos los simbolos

    def contractUpdateTicks(self, reqId):
        # Tenemos por un lado los contratos BAG
        #  y luego hay que actualizar los legs por si alguno tiene este reqId
        # Los que no son BAG tambien tienren el contractReqIdLegs con 1 solo entry, por lo que se buscan los dos igual
        for contrato in self.contractList_:
            updated = False
            for conReqLeg in contrato['contractReqIdLegs']:
                if conReqLeg['reqId'] == reqId:
                    updated = True
            if updated:
                price2sell = 0
                price2buy = 0
                price2last = 0
                size2sell = None
                size2buy = None
                size2last = None
                for conReqLeg in contrato['contractReqIdLegs']:      
                    allReady = True
                    if conReqLeg['reqId'] == None:
                        allReady = False
                        break
                    legReqId = conReqLeg['reqId']
                    if not legReqId in self.tickPrices_:
                        allReady = False
                        break
                    if not 'BID' in self.tickPrices_[legReqId] or not 'ASK' in self.tickPrices_[legReqId]:  
                        allReady = False
                        break
                    if not 'BID_SIZE' in self.tickPrices_[legReqId] or not 'ASK_SIZE' in self.tickPrices_[legReqId]:  
                        allReady = False
                        break
                    if not 'LAST' in self.tickPrices_[legReqId] or not 'LAST_SIZE' in self.tickPrices_[legReqId]:  
                        allReady = False
                        break
                    if conReqLeg['action'] == 'BUY':
                        price2sell = price2sell + self.tickPrices_[legReqId]['BID'] * conReqLeg['ratio']
                        price2buy = price2buy + self.tickPrices_[legReqId]['ASK'] * conReqLeg['ratio']
                        if 'LAST' in self.tickPrices_[legReqId]:
                            price2last = price2last + self.tickPrices_[legReqId]['LAST'] * conReqLeg['ratio']
                    if conReqLeg['action'] == 'SELL':
                        price2sell = price2sell - self.tickPrices_[legReqId]['ASK'] * conReqLeg['ratio']
                        price2buy = price2buy - self.tickPrices_[legReqId]['BID'] * conReqLeg['ratio']
                        if 'LAST' in self.tickPrices_[legReqId]:
                            price2last = price2last - self.tickPrices_[legReqId]['LAST'] * conReqLeg['ratio']
                    if size2sell == None:
                        size2sell = self.tickPrices_[legReqId]['BID_SIZE']
                    else:
                        size2sell = min(size2sell, self.tickPrices_[legReqId]['BID_SIZE'])
                    if size2buy == None:
                        size2buy = self.tickPrices_[legReqId]['ASK_SIZE']
                    else:
                        size2buy = min(size2buy, self.tickPrices_[legReqId]['ASK_SIZE'])

                    if 'LAST_SIZE' in self.tickPrices_[legReqId]:
                        if size2last == None:
                            size2last = self.tickPrices_[legReqId]['LAST_SIZE']
                        else:
                            size2last = min(size2last, self.tickPrices_[legReqId]['LAST_SIZE'])
                if allReady == False:
                    price2sell = None
                    price2buy = None
                    price2last = None
                    size2buy = None
                    size2sell = None
                    size2last = None

                contrato['currentPrices']['BUY'] = price2buy
                contrato['currentPrices']['SELL'] = price2sell
                contrato['currentPrices']['LAST'] = price2last
                contrato['currentPrices']['BUY_SIZE'] = size2buy
                contrato['currentPrices']['SELL_SIZE'] = size2sell
                contrato['currentPrices']['LAST_SIZE'] = size2last

                if allReady != False:
                    # Aquí habría que actualizar la DB para el contrato['gConId'] con estos datos:
                    gConId = contrato['gConId']
                    #lSymbol = contrato['contract'].localSymbol
                    lSymbol = self.contractSummaryBrief (gConId)
                    timestamp = datetime.datetime.now()
                    data_args = {'gConId': gConId, 'Symbol':lSymbol, 'timestamp':timestamp, 
                                 'BID': price2sell, 'ASK':price2buy, 'LAST':price2last,
                                 'BID_SIZE': size2sell, 'ASK_SIZE':size2buy, 'LAST_SIZE':size2last
                                 }
                    contrato['dbPandas'].dbUpdateAdd(data_args)

    def contractGetCurrentPricesPerGconId (self, gConId):
        for contrato in self.contractList_:
            if contrato['gConId'] == gConId:
                return contrato['currentPrices']
        return None


    def contractCheckIfExists (self, gConId):
        for contrato in self.contractList_:
            if contrato['gConId'] == gConId:
                return True
        return False

    def contractGetContractbyGconId (self, gConId):
        for contrato in self.contractList_:
            if contrato['gConId'] == gConId:
                return contrato
        
        return None

    def contractGetGconId(self, contractObj):
        if contractObj == "" or contractObj == None:
            return None

        gConId = ''

        if contractObj.secType == "BAG" and len(contractObj.comboLegs) > 0:
            for leg in contractObj.comboLegs:
                gConId += str(leg.conId)
        else:
            gConId = str(contractObj.conId)
        
        return int(gConId)

    def contractGetBySymbol(self, symbol):
        for contrato in self.contractList_:
            conSymbol = self.contractSummaryBrief(contrato['gConId'])
            if conSymbol == symbol:
                return contrato
        return None

    def contractSubscribeTickPrice(self, contractReqIdLeg): 

        if contractReqIdLeg['reqId'] != None:
            return contractReqIdLeg['reqId']
        else: # Para el reqMktData el Contract tiene que ser virgen sin conid
            contrato = self.contractGetContractbyGconId(contractReqIdLeg['conId'])
            if contrato['contract'].secType == 'FUT':
                code = contrato['contract'].symbol + 'Z2' # Me invento lo de Z2 y reescribo despues el lasttrade...
                contrato1 = self.appObj_.contractSimpleFUTcreate(code)
                contrato1.lastTradeDateOrContractMonth = contrato['contract'].lastTradeDateOrContractMonth
            else: # Asumo STK
                code = contrato['contract'].symbol
                contrato1 = self.appObj_.contractSTKcreate(code)
            reqId = self.appObj_.reqMktDataGen (contrato1)  # A la API no se le puede mandar contrato, sino uno nuevo sin conId
            contractReqIdLeg['reqId'] = reqId
            return reqId

    def contractGetSymbolsIfFullLegsDataByGconId (self, gConId):
        simbolos = []
        simbolo = {}

        for contrato in self.contractList_:
            if contrato['gConId'] == gConId and contrato['fullLegData']:
                if contrato['contract'].secType == "BAG":
                    for leg in contrato['contract'].comboLegs:
                        exists = False
                        for contratoLeg in self.contractList_:
                            if contratoLeg['contract'].conId == leg.conId:  
                                simbolo = {'conId': contratoLeg['contract'].conId, 'reqId': None, 'ratio': leg.ratio, 'action': leg.action, 'lSymbol': contratoLeg['contract'].localSymbol}
                                simbolos.append(simbolo)
                                exists = True
                                break
                        if not exists:  # Si alguno no existe, devolvemos lista vacia
                            simbolos = []
                            return simbolos
                else:
                    simbolo = {'conId': contrato['contract'].conId, 'reqId': None, 'ratio': 1, 'action': 'BUY', 'lSymbol': contrato['contract'].localSymbol}
                    simbolos.append(simbolo)
                break
        return simbolos

    def contractListAll (self):
        # Esto igual no hace falta y devuelvo toda la lista
        lista = []
        contratoDict = {}
        for contrato in self.contractList_:
            contratoDict['conId'] = contrato['contract'].conId
            contratoDict['symbol'] = contrato['contract'].localSymbol
            contratoDict['secType'] = contrato['contract'].secType
            if contrato['contract'].secType == "BAG":
                contratoDict['symbolBag'] = self.contractSummaryBrief (contrato['gConId'])
            else:
                contratoDict['symbolBag'] = ''
            contratoDict['legs'] = []



    def contractSummaryAllFull (self):
        summaryStr = ''
        for contrato in self.contractList_:
            summaryStr += self.contractSummaryFull (contrato['gConId'])

        return summaryStr

    def contractSummaryAllBrief (self):
        summaryStr = ''
        for contrato in self.contractList_:
            summaryStr += self.contractSummaryBrief (contrato['gConId'])

        return summaryStr

    def contractSummaryAllBriefWithPrice (self):
        summaryStr = ''
        for contrato in self.contractList_:
            logging.debug ('gConID: %s',  str(contrato['gConId']))
            summaryStr += '[' + str(contrato['gConId']) + '] - '
            summaryStr += self.contractSummaryBriefWithPrice (contrato['gConId'])
            summaryStr += '\n'

        return summaryStr

    def contractSummaryBriefWithPrice (self, gConId):
        summaryStr = ''
        summaryStr += self.contractSummaryBrief(gConId)
        summaryStr += ', ' + self.contractSummaryPricesOnly(gConId)

        return summaryStr

    def contractSummaryFullWithPrice (self, gConId):
        summaryStr = ''
        summaryStr += self.contractSummaryFull(gConId)
        summaryStr += '         ' + self.contractSummaryPricesOnly(gConId)

        return summaryStr


    def contractSummaryPricesOnly (self, gConId):

        prices = {}
        prices = self.contractGetCurrentPricesPerGconId(gConId)

        priceBuy = 'Na'
        priceSell = 'Na'
        priceLast = 'Na'
        if not prices['BUY'] is None:
            priceBuy = floatMaxString(prices['BUY'])
        if not prices['SELL'] is None:
            priceSell = floatMaxString(prices['SELL'])
        if not prices['LAST'] is None:
            priceLast = floatMaxString(prices['LAST'])
        
        summaryStr = 'Price (BUY/SELL/LAST): ' + priceBuy + '/' + priceSell + '/' + priceLast

        return summaryStr
  
    def contractSummary (self, gConId):
        
        if self.verboseBrief == True:
            return (self.contractSummaryBrief (gConId))
        else:
            return (self.contractSummaryFull (gConId))

    def contractSummaryFull (self, gConId):
        result = True
        summaryStr = ''
            
        for contrato in self.contractList_:
            if contrato['gConId'] == gConId:
                summaryStr += '     Contrato:\n'
                summaryStr += '         gConId:' + str(contrato['gConId']) + '\n'
                summaryStr += '         ConId: ' + str(contrato['contract'].conId) + '\n'
                summaryStr += '         Symbol: ' + str(contrato['contract'].localSymbol) + '\n'
                summaryStr += '         SecType: ' + str(contrato['contract'].secType) + '\n'
                if contrato['contract'].secType == "BAG":
                    summaryStr += ''
                    for leg in contrato['contract'].comboLegs:
                        sstr = self.legSummary(leg, contrato['contract'].symbol)
                        summaryStr += sstr

                elif contrato['contract'].secType == "FUT":
                    summaryStr += '         Date: ' + str(contrato['contract'].lastTradeDateOrContractMonth) + '\n'
                break
        return summaryStr
                
    def contractSummaryBrief (self, gConId):
        result = True
        summaryStr = ''
        for contrato in self.contractList_:
            if contrato['gConId'] == gConId:
                if contrato['contract'].secType == "BAG":
                    spreadInfoList = [] 
                    # No me fio del orden de los combolegs. Lo meto en una lista volatil, se ordena e imprime
                    for leg in contrato['contract'].comboLegs:
                        spreadLocalSymbol, spreadDate = self.legSummaryBriefExtract(leg, contrato['contract'].symbol)
                        spreadAction = leg.action
                        spreadRatio = leg.ratio
                        spreadInfoList.append({"localSymbol":spreadLocalSymbol, "Action":spreadAction, "Ratio": spreadRatio, "Date":spreadDate})

                    summaryStr = self.legSummaryBriefSort (spreadInfoList)
                        
                else:
                    summaryStr = contrato['contract'].localSymbol
                break
                
        return summaryStr
        
    def legSummary (self, leg, symbol):
        result = True
        exists = False
        summaryStr = ''
        
        
        contrato1 = Contract() 
        for contrato in self.contractList_:
            if contrato['contract'].conId == leg.conId:
                contrato1 = contrato['contract']
                exists = True
                break
        
        summaryStr += '         Leg:\n'
        summaryStr += '             ConId: ' + str(leg.conId) + '\n'
        summaryStr += '             Action: ' + str(leg.action) + '\n'
        summaryStr += '             Symbol: ' + str(symbol) + '\n'
        summaryStr += '             Ratio: ' + str(leg.ratio) + '\n'
        if exists == True:
            summaryStr += '             LocalSymbol: ' + str(contrato1.localSymbol) + '\n'
            summaryStr += '             LastOrderDate: ' + str(contrato1.lastTradeDateOrContractMonth) + '\n'
                            
        return summaryStr  
        
    def legSummaryBriefExtract (self, leg, symbol):   
        exists = False
        contrato1 = Contract()
        for contrato in self.contractList_:
            if contrato['contract'].conId == leg.conId:  
                contrato1 = contrato['contract']
                exists = True
                break

        lsymbol = None
        LTD = None
        if not exists:
            lsymbol = symbol
            LTD = 0
        else:
            lsymbol = contrato1.localSymbol
            LTD = contrato1.lastTradeDateOrContractMonth

        return lsymbol, LTD

    def legSummaryBriefSort (self, spreadInfoList):   
        spreadSize = len(spreadInfoList)
        summaryStr = ''
        if spreadSize == 2:
            if spreadInfoList[0]['Date'] > spreadInfoList[1]['Date']:
                spreadInfoList[0], spreadInfoList[1] = spreadInfoList[0], spreadInfoList[1]
            summaryStr = self.legSummaryBriefString(spreadInfoList)
        if spreadSize == 3:
            # Asumo que hay 2 BUY y 1 SELL
            if spreadInfoList[0]['Action'] == 'SELL':
                spreadInfoList[0], spreadInfoList[1] = spreadInfoList[0], spreadInfoList[1]
            if spreadInfoList[2]['Action'] == 'SELL':
                spreadInfoList[1], spreadInfoList[2] = spreadInfoList[2], spreadInfoList[1]
            if spreadInfoList[0]['Date'] > spreadInfoList[2]['Date']:
                spreadInfoList[0], spreadInfoList[2] = spreadInfoList[2], spreadInfoList[0]
            summaryStr = self.legSummaryBriefString(spreadInfoList)
            
            
            
        return summaryStr
        
    def legSummaryBriefString (self, spreadInfoList):   
        spreadSize = len(spreadInfoList)
        summaryStr = ''
        nItem = 0
        for parte in spreadInfoList:
            if parte['Action'] == 'SELL':
                summaryStr += '-'
            elif nItem > 0:
                summaryStr += '+'
            if int(parte['Ratio']) > 1:
                summaryStr += str(parte['Ratio'])
            summaryStr += parte['localSymbol']
            nItem += 1
                        
        return summaryStr

    ########################################
    # orders

    def orderAdd (self, contractObj, orderObj, paramsDict):
        result = False
        
        if contractObj == "":
            contractObj = Contract()
            
        if orderObj == "":
            orderObj = Order()
        
        orden = {}
        orden['permId'] = orderObj.permId
        orden['contractId'] = self.contractGetGconId(contractObj)
        orden['order'] = orderObj
        orden['params'] = paramsDict
        orden['toPrint'] = False
        str_o = self.orderSummary(orden)
        logging.info (str_o)
        
        try:
            self.orderList_.append(orden)
            result = True
        except:
            self.error(900, "Error añadiendo orden")

        self.orderCheckIfRemove(orden) # No deberia ser necesario nunca aqui
            
        return (result)

    def orderUpdate (self, data):
        tempId = data['orderId']
        contractObj = data['contractObj']
        orderObj = data['orderObj']
        paramsDict = data['paramsDict']
        result = True
        exists = False
        
        # Find permId from tempId        
        localPermId = self.orderGetPermId (tempId, orderObj, paramsDict)
        if localPermId == "":
            return (False)
        
        if not contractObj == "":
            #print ('Actualizo cont')
            self.contractAdd (contractObj)         # Normalmante al añadir la orden, añadimos y actualizamos el contrato    
        
        for orden in self.orderList_:
            if orden['permId'] == localPermId:
                exists = True
                try:
                    if not contractObj=="":
                        orden['contractId'] = self.contractGetGconId(contractObj)
                    if not orderObj=="":
                        orden['order'] = orderObj
                    if not paramsDict=="":
                        orden['params'].update(paramsDict)
                    #orden['toPrint'] = True
                    str_o = self.orderSummary(orden)
                    logging.info (str_o)
                    self.orderCheckIfRemove(orden)
                except:
                    logging.error ('Error actualizando orden')
                break
                
        if not exists:
            result = self.orderAdd (contractObj, orderObj, paramsDict)

        return (result)
    
    def orderCheckIfRemove (self, orden):
        # Despues de un update, mirar si hay que borrarla
        if 'status' in orden['params']:
            if orden['params']['status'] == 'Cancelled':
                self.orderList_.remove(orden)
            if orden['params']['status'] == 'Filled':
                self.orderList_.remove(orden)

    def orderGetPermId (self, tempId, orderObj, paramsDict):
        
        # Find permId from tempId
        localPermId = ""
        if not orderObj=="":
            localPermId = orderObj.permId
        elif 'permId' in paramsDict and paramsDict['permId'] != '':
            localPermId = paramsDict['permId']
        else:
            for orden in self.orderList_:
                if orden['order'].orderId == tempId:
                    localPermId = orden['order'].permId
                    break
        
        return (localPermId)

    def orderGetByOrderId (self, orderId):
        for orden in self.orderList_: 
            if orden['order'].orderId == orderId:
                return orden

    def orderGetByGconId (self, gConId):
        ordenes = []
        for orden in self.orderList_: 
            if orden['contractId'] == gConId:
                ordenes.append(orden)
        return ordenes

        
    def orderDeleteAll (self):
        for orden in self.orderList_: 
            self.orderList_.remove(orden)
        self.orderList_ = []

    def orderCheckIfExistsByOrderPermId (self, orderPermId):
        for order in self.orderList_: 
            if int(order['permId']) == int(orderPermId):
                return True
        return False

    def orderCheckIfExistsByOrderId (self, orderId):
        for order in self.orderList_: 
            if int(order['order'].orderId) == int(orderId):
                return True
        return False


    def orderSummaryAllBrief (self):
        summaryStr = ''
        
        for orden in self.orderList_:
            summaryStr += self.orderSummaryBrief (orden)

        return summaryStr

    def orderSummaryAllUpdated (self):
        result = True
        summaryStr = ''
        
        for orden in self.orderList_:
            if orden['toPrint'] == True:
                summaryStr += self.orderSummary (orden)

        return summaryStr

    def orderSummaryFullByOrderId (self, orderId):
        result = True
        summaryStr = ''
        
        for orden in self.orderList_:
            if orden['order'].orderId == int(orderId):
                summaryStr = self.orderSummaryFull (orden)
        return summaryStr
        
    def orderSummary (self, orden):        
        if self.verboseBrief == True:
            return (self.orderSummaryBrief (orden))
        else:
            return (self.orderSummaryFull (orden))

    def orderSummaryFull (self, orden):
        summaryStr = ''
        
        summaryStr  = '--------------------------------------\n'
        summaryStr += 'Orden ' + str(orden['order'].orderId) + ' actualizada\n'
        summaryStr += '     Orden:\n'
        summaryStr += '         PermId:' + str(orden['order'].permId) + '\n'
        summaryStr += '         Action:' + str(orden['order'].action) + '\n'
        summaryStr += '         Qty:' + str(orden['order'].totalQuantity) + '\n'
        if 'status' in orden['params']:
            summaryStr += '         Status:' + str(orden['params']['status']) + '\n'
        if 'filled' in orden['params']:
            summaryStr += '         Filled:' + str(orden['params']['filled']) + '\n'
        if 'remaining' in orden['params']:
            summaryStr += '         Remaining:' + str(orden['params']['remaining']) + '\n'
        if 'lastFillPrice' in orden['params']:
            summaryStr += '         LastFillPrice:' + str(orden['params']['lastFillPrice']) + '\n'

        summaryStr += '         ' + self.contractSummaryPricesOnly(orden['contractId']) + '\n'
        summaryStr += self.contractSummaryFull(orden['contractId'])
        summaryStr += '--------------------------------------\n'

        orden['toPrint'] = False

        return summaryStr
        
    def orderSummaryBrief (self, orden):
        summaryStr = ''
        status = ''
        filled =''
        remaining = ''
        lastFillPrice = ''
        
        if 'status' in orden['params']:
            status = str(orden['params']['status'])
        if 'filled' in orden['params']:
            filled = str(orden['params']['filled'])
        if 'remaining' in orden['params']:
            remaining = str(orden['params']['remaining'])
        if 'lastFillPrice' in orden['params']:
            lastFillPrice = str(orden['params']['lastFillPrice'])
            
        summaryStr = '[Orden (' + str(orden['order'].orderId) + ')] "' + self.contractSummaryBrief(orden['contractId']) + '" '
        summaryStr += str(orden['order'].action)
        summaryStr += ' (' + status + ')'
        summaryStr += ', Qty: ' + str(orden['order'].totalQuantity)
        summaryStr += '(' + filled + '/' + remaining + ') Last Price: ' +  lastFillPrice
        
        summaryStr += ', ' + self.contractSummaryPricesOnly(orden['contractId'])

        summaryStr += '\n'
        orden['toPrint'] = False
                
        return summaryStr
                
 