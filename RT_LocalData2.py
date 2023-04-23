#from typing_extensions import Self
from ibapi.contract import *
from ibapi.order import *
from ibapi.utils import floatMaxString, longMaxString
from ibapi.common import UNSET_INTEGER, UNSET_DOUBLE, UNSET_LONG, UNSET_DECIMAL, DOUBLE_INFINITY, INFINITY_STR
import strategiesNew
import pandasDB
import logging
import datetime
import influxAPI

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
    #    contractReqIdLegs: Lista de dicts: [{'conId': , 'reqId': None, 'reqIdPnL': None, 'ratio': , 'action':, 'lSymbol':  },...]
    #    currentPrices: Precios actuales ({'BUY': 10, 'SELL': 10.2, 'LAST': 10.1})
    #    hasContractSymbols: Si ya tengo los HEJ3 para seguir los ticks. Necesito quer fulllegdata= True para poder pedirlos y tener esto a True.
    #
    # orderList_:
    #    permId: permanentId de la orden en IB
    #    contractId: gConId
    #    order: orderObj de IB
    #    params: Dict de params que se reciben como paramateros 
    #    toPrint: Algo ha cambiado y hay que imprimir o webFE
    #    toCancel: Orden que hay que cancelar
    # 
    # tickPrices_:
    #    Key: reqId ['12'] ---> {12: {'BID': 10, 'ASK': 10.1, 'LAST': 10.1, 'HIGH': 11, 'LOW': 9, 'OPEN':10.5, 'CLOSE': 10.2}}
    #
    # pnl_:
    #    Key: reqIdPnL ['11'] ---> {11: {'dailyPnL':dailyPnL, 'unrealizedPnL':unrealizedPnL, 'realizedPnL':realizedPnL}}
    #
    def __init__(self):
        self.verboseBrief = False
        self.appObj_ = None
        self.wsServerInt_ = None
        self.strategies_ = None # Se inicializa desde Local_Daemon llamando al constructor dr Strategies, y ese lo copia aqui
        self.influxIC_ = influxAPI.InfluxClient()

        self.accountData_ = {}
        self.orderList_ = []  # includes orders and contracts (hay que sacar los contracts a puntero externo, y los usan las posiciones)
        #self.contractList_ = []  # Directamente lista de contracts
        self.contractDict_ = {}  # Directamente dict de contracts

        self.tickPrices_ = {}    # Key: reqId ['12'] ---> {12: {'BID': 10, 'ASK': 10.1, 'LAST': 10.1, 'HIGH': 11, 'LOW': 9, 'OPEN':10.5, 'CLOSE': 10.2}}
        self.pnl_ = {}

        self.contractInconplete_ = False

    ########################################
    # Executions

    # Deberíamos tener un Pandas+CSV que guarde todas las execs.
    # Si se pierde la conexsión habría que pedir todas y comparar

    def executionAnalisys (self, data):
        #Podemos hacer más cosas, de momento solo informamos a las estrategias
        
        self.strategies_.strategyIndexOrderExecuted(data)   # Esto entra a traves de la orden

    def commissionAnalisys (self, data):
        #Podemos hacer más cosas, de momento solo informamos a las estrategias
        
        self.strategies_.strategyIndexOrderCommission(data)   # Esto entra a traves de la orden

    ########################################
    # Account

    def accountTagUpdate (self, data):

        reqId = data['reqId']
        if 'end' in data:
            logging.info ("Ya tengo la account info:\n%s", self.accountSummary())
            return # no hay nada mas. Ha terminado y punto (mirar IB_API_Client)
        account = data['account']
        tag = data['tag']
        value = data['value']

        dictLocal = {}
        dictLocal[tag] = value
        dictLocal['accountId'] = account
        self.accountData_.update (dictLocal)


    def accountSummary (self):
        summaryStr = ''
        for tag in self.accountData_:
            summaryStr += str(tag) + ": " + str(self.accountData_[tag]) + '\n'
        return summaryStr

    ########################################
    # Positions


      
    def positionUpdate (self, data):
        contractObj = data['contract']
        nPosition = data['position']
        avgCost = data['avgCost']
        result = True

        if not contractObj == "":
            #print ('Actualizo cont')
            self.contractAdd (contractObj)

        gConId = self.contractGetGconId(contractObj)

        logging.info("[Posicion] Actualizada %s: %d", contractObj.localSymbol, nPosition)

        self.contractDict_[gConId]['pos'] = nPosition  # Solo haría falta esto cuando lo pase todo.
        self.contractDict_[gConId]['posAvgPrice'] = avgCost

        self.postionFixSpreads()
         
                        
        return (result)

    def postionFixSpreads (self):
        for gConId, contrato in self.contractDict_.items():
            #Repaso todas la bags para ver si cada contrato individual tiene posiciones
            if contrato['contract'].secType == "BAG":
                pos_min = None
                # Busco las posiciones mínimas que tienen todos los legs.
                # Hay que comprobar que son todas en el mismo sentodo (con la correcccion del ratio)
                # contractReqIdLegs: Lista de dicts: [{'conId': , 'reqId': None, 'reqIdPnL': None, 'ratio': , 'action':, 'lSymbol':  },...]
                logging.debug("Compruebo BAG %s", contrato['fullSymbol'])

                for contractLegInfo in contrato['contractReqIdLegs']:
                    conId = contractLegInfo['conId']
                    ratio = contractLegInfo['ratio']
                    if contractLegInfo['action'] == 'SELL':
                        ratio = (-1) * ratio # Normalizando a siempre positivo (BUY) o siempre negativo (SELL)
                    
                    currPosLeg = self.contractDict_[conId]['pos'] 
                    if not currPosLeg:
                        currPosLeg = 0
                    pos_corrected = int(currPosLeg / ratio)

                    if pos_min == None:  # Para el primero. Seguro que hay mejores maneras de hacerlo.
                        pos_min = pos_corrected
                    elif pos_corrected * pos_min >= 0:  # Esto es para comprobar que son del mismo signo. Si no no nos vale, hayq que respetar el SELL/BUY de cada leg
                        pos_min = min ([pos_corrected, pos_min], key = abs)  # key=abs por si son negativol (BAG en SELL)
                    else: 
                        pos_min = 0 # No son del mismo signo, no nos vale
                    logging.debug("      %s: %d(%d)", contractLegInfo['lSymbol'], currPosLeg, pos_min)
                # pos_min es las que tengo que robar (multiplicado por el ratio de cada uno) a cada conId, para darselo al BAG
                if pos_min != 0: # Hay algo
                    logging.info("Actualizo BAG %s con esta position: %d", contrato['fullSymbol'], pos_min)
                    avgPrice = 0
                    for contractLegInfo in contrato['contractReqIdLegs']:
                        conId = contractLegInfo['conId']
                        ratio = contractLegInfo['ratio']
                    
                        if contractLegInfo['action'] == 'SELL':
                            ratio = (-1) * ratio # Normalizando a siempre positivo (BUY) o siempre negativo (SELL)

                        avgPrice += self.contractDict_[conId]['posAvgPrice'] * ratio

                        deltaPos = pos_min * ratio
                        self.contractDict_[conId]['pos'] -= int(deltaPos)
                        if self.contractDict_[conId]['pos'] == 0:
                            self.contractDict_[conId]['posAvgPrice'] = 0

                        logging.info("      %s: %d", contractLegInfo['lSymbol'], deltaPos)
                    #Finalmente, pongo pos_min al BAG
                    if contrato['pos'] == None: # Inicializamos
                        contrato['pos'] = 0
                    contrato['pos'] = int(pos_min)
                    contrato['posAvgPrice'] = avgPrice

    def positionDeleteAll (self):
        # Pasar por contracts y borrar posiciones
        for gConId, contrato in self.contractDict_.items():
            contrato['pos'] = None
            contrato['posAvgPrice'] = None

    def positionSummaryBrief (self, gConId):
        summaryStr = ''
        
        summaryStr = '[Posicion] - ' + self.contractDict_[gConId]['fullSymbol']
        summaryStr += ', Qty: ' +  longMaxString(self.contractDict_[gConId]['pos']) + ', AvgCost: ' + floatMaxString(self.contractDict_[gConId]['posAvgPrice'])

        summaryStr += ', ' + self.contractSummaryPricesOnly(gConId)

        #self.positionSetSymbolsIfNeeded (posicion)  


    ########################################
    # tickPrice
    #   Key: reqId ['12'] ---> {12: {'BID': 10, 'ASK': 10.1, 'LAST': 10.1, 'HIGH': 11, 'LOW': 9, 'OPEN':10.5, 'CLOSE': 10.2}}
        
    def tickUpdatePrice (self, data):
        reqId = data['reqId']
        tickType = data['tickType']
        price = None
        if 'price' in data:
            price = round(data['price'],5)  # bajo a 5 decimales
            if price == -100 or price == 0:  # Indica que no está disponible
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
            self.tickPrices_[reqId] = prices
        if size != None:
            bChange = False
            if tickType == 0 or tickType == 69:
                bChange = True
                prices['BID_SIZE'] = size
            if tickType == 3 or tickType == 70:
                bChange = True
                prices['ASK_SIZE'] = size  
            if tickType == 5 or tickType == 71:
                if size != 0 or ('LAST' in prices and prices['LAST'] != 0):  # Debería ser un and?
                    bChange = True
                    prices['LAST_SIZE'] = size
            if tickType == 8 or tickType == 74:
                bChange = True
                prices['VOLUME'] = size

            
        
            self.tickPrices_[reqId] = prices
        
            if bChange:  # Solo con size
                logging.debug("Deberia actualizar valor")
                self.contractUpdateTicks(reqId)

    ########################################
    # PnL Update
    #   Key: reqIdPnL ['11'] ---> {11: {'dailyPnL':dailyPnL, 'unrealizedPnL':unrealizedPnL, 'realizedPnL':realizedPnL, 'pos': pos, 'value':value}}
        
    def pnlUpdate (self, data):
        # data = {'reqId': reqId, 'pos': pos, 'dailyPnL':dailyPnL, 'unrealizedPnL':unrealizedPnL, 'realizedPnL':realizedPnL, 'value':value}
        reqIdPnL = data['reqId']        
        pnlType = data['pnlType']

        logging.debug ('PnL actualizado (req: %d):', reqIdPnL)
        logging.debug ('    dailyPnL: %d', data['dailyPnL'])
        logging.debug ('    realizedPnL: %d', data['realizedPnL'])
        logging.debug ('    unrealizedPnL: %d', data['unrealizedPnL'])
        if pnlType == 'single':
            logging.debug ('    Pos: %d', data['pos'])
            logging.debug ('    Value: %d', data['value'])


        pnl = {}
        if reqIdPnL in self.pnl_:
            pnl = self.pnl_[reqIdPnL]

        pnl['pnlType'] = pnlType

        bChange = False

        for k,v in data.items():
            if v == UNSET_DOUBLE:  # Este valor lo usa IB para indicar empty cell.
                continue
            if k not in ['reqId']: # no quiero usar este key
                if k not in pnl:
                    bChange = True
                    pnl[k] = v
                elif v != pnl[k]:
                    bChange = True
                    pnl[k] = v

        self.pnl_[reqIdPnL] = pnl

        if bChange:  # Solo con size
            logging.debug("Deberia actualizar los PnL")
            if pnlType == 'single':
                self.contractUpdatePnL(reqIdPnL)

    ########################################
    # contracts
       
    def contractAdd (self, contractObj):
        if contractObj == "" or contractObj == None:
            return
        #contractDict_
        # {'1234455':{'contact':contractobj, 'pos':pos....}, }
        gConId = self.contractGetGconId(contractObj)

        if gConId in self.contractDict_:
            if self.contractDict_[gConId]['contract'].conId == 0:
                self.contractDict_[gConId]['contract'].conId = contractObj.conId
            return

        contrato = {}
        contrato['gConId'] = gConId
        contrato['fullSymbol'] = None
        contrato['contract'] = contractObj
        contrato['pos'] = None
        contrato['posAvgPrice'] = None
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
        contrato['currentPrices']['updated'] = False # Para saber si hay que actualizar alguna presentacion de precios (web)
        contrato['pnl'] = {}
        contrato['pnl']['dailyPnL'] = None
        contrato['pnl']['unrealizedPnL'] = None
        contrato['pnl']['realizedPnL'] = None
        contrato['pnl']['value'] = None
        contrato['pnl']['updated'] = None
        contrato['hasContractSymbols'] = False

        self.contractDict_[gConId] = contrato    

    def contratoReturnDictAll(self):
        return self.contractDict_

    def contractCheckStatus (self):
        missing = False

        for gConId, contrato in self.contractDict_.items():
            if self.contractCheckIfIncompleteSingle(contrato):    # 1.- Si no tiene los legs, upstream lo tiene que arreglar
                missing = True
            elif not contrato['hasContractSymbols']:              # 2.- Si no tiene symbols, se buscan
                self.contractSetSymbolsIfNeeded(contrato)
            else:                                                 # 3.- Si tiene los symbols, asegurar que estan subscritos a tick
                self.contractSubscribeIfNeeded(contrato)
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

        for gConId, contrato in self.contractDict_.items():
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
        for gConId, contrato in self.contractDict_.items():
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
        file1 = open('strategies/ContractsWatchList.conf', 'r')
        Lines = file1.readlines()
  
        for line in Lines:
            if line.rstrip() == '':
                continue
            contractN = self.appObj_.contractFUTcreate(line.rstrip())
            self.contractAdd(contractN)

    def contractWriteFixedWatchlist (self, contractList):
        with open('strategies/ContractsWatchList.conf', 'w') as f:
            for line in contractList:
                f.writelines(line + '\n')

    def contractReturnFixedWatchlist (self):
        file1 = open('strategies/ContractsWatchList.conf', 'r')
        Lines = file1.readlines()
        contractList = []
  
        for line in Lines:
            contractList.append(line.rstrip())

        return contractList

    def contractUnsubscribeAll (self):
        for gConId, contrato in self.contractDict_.items():
            for contractReqIdLeg in contrato['contractReqIdLegs']:
                contractReqIdLeg['reqId'] = None
                contractReqIdLeg['reqIdPnL'] = None  
        for reqId in self.tickPrices_:
            self.appObj_.cancelMktDataGen (reqId)
        self.tickPrices_ = {}
        for reqId in self.pnl_:
            self.appObj_.cancelPnLSingle (reqId)
        self.pnl_ = {}

    def contractSubscribeIfNeeded (self, contrato):
        for contractReqIdLeg in contrato['contractReqIdLegs']:
            contractReqIdLeg['reqId'] = self.contractSubscribeTickPrice (contractReqIdLeg)
            contractReqIdLeg['reqIdPnL'] = self.contractSubscribePnL (contractReqIdLeg)

    def contractSetSymbolsIfNeeded(self, contrato):
        contrato['contractReqIdLegs'] = self.contractGetSymbolsIfFullLegsDataByGconId(contrato['gConId'])
        # contrato['contractReqIdLegs'] --> [{'conId': , 'reqId': None, 'reqIdPnL':None, 'ratio': , 'action': , 'lSymbol': },...]
        if len(contrato['contractReqIdLegs']) > 0:
            contrato['hasContractSymbols'] = True
            lSymbol = self.contractSummaryBrief (contrato['gConId'])     
            contrato['fullSymbol'] = lSymbol      
            contrato['dbPandas'] = pandasDB.dbPandasContrato (lSymbol, self.influxIC_)           # No se puede hasta que no tenga todos los simbolos
            # Pillo los ultimos precios guardados en DB
            logging.info ('Pido precios de BD para %s', lSymbol)
            lastPrices = contrato['dbPandas'].dbGetLastPrices()
            logging.info ('    LAST: %s', lastPrices['LAST'])
            contrato['currentPrices']['BUY'] = lastPrices['ASK']
            contrato['currentPrices']['SELL'] = lastPrices['BID']
            contrato['currentPrices']['LAST'] = lastPrices['LAST']
            contrato['currentPrices']['BUY_SIZE'] = lastPrices['ASK_SIZE']
            contrato['currentPrices']['SELL_SIZE'] = lastPrices['BID_SIZE']
            contrato['currentPrices']['LAST_SIZE'] = lastPrices['LAST_SIZE']


    def contractUpdateTicks(self, reqId):
        # Tenemos por un lado los contratos BAG
        #  y luego hay que actualizar los legs por si alguno tiene este reqId
        # Los que no son BAG tambien tienren el contractReqIdLegs con 1 solo entry, por lo que se buscan los dos igual
        for gConId, contrato in self.contractDict_.items():
            updated = False
            for conReqLeg in contrato['contractReqIdLegs']: # Directamente esto implica que contrato['hasContractSymbols'] = True
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
                        price2last = price2last + self.tickPrices_[legReqId]['LAST'] * conReqLeg['ratio']
                        if size2sell == None:
                            size2sell = int(self.tickPrices_[legReqId]['BID_SIZE'] / conReqLeg['ratio'])   
                        else:
                            size2sell = min(size2sell, int(self.tickPrices_[legReqId]['BID_SIZE'] / conReqLeg['ratio']))
                        if size2buy == None:
                            size2buy = int(self.tickPrices_[legReqId]['ASK_SIZE'] / conReqLeg['ratio'])
                        else:
                            size2buy = min(size2buy, int(self.tickPrices_[legReqId]['ASK_SIZE'] / conReqLeg['ratio']))
                    if conReqLeg['action'] == 'SELL':
                        price2sell = price2sell - self.tickPrices_[legReqId]['ASK'] * conReqLeg['ratio']
                        price2buy = price2buy - self.tickPrices_[legReqId]['BID'] * conReqLeg['ratio']
                        price2last = price2last - self.tickPrices_[legReqId]['LAST'] * conReqLeg['ratio']
                        if size2sell == None:
                            size2sell = int(self.tickPrices_[legReqId]['ASK_SIZE'] / conReqLeg['ratio'])
                        else:
                            size2sell = min(size2sell, int(self.tickPrices_[legReqId]['ASK_SIZE'] / conReqLeg['ratio']))
                        if size2buy == None:
                            size2buy = int(self.tickPrices_[legReqId]['BID_SIZE'] / conReqLeg['ratio'])
                        else:
                            size2buy = min(size2buy, int(self.tickPrices_[legReqId]['BID_SIZE'] / conReqLeg['ratio']))
                
                    if size2last == None:
                        size2last = int(self.tickPrices_[legReqId]['LAST_SIZE'] / conReqLeg['ratio'])
                    else:
                        size2last = min(size2last, int(self.tickPrices_[legReqId]['LAST_SIZE'] / conReqLeg['ratio']))

                    if not size2buy:  # Por si son None, les paso a 0 ( no debería, pero así aseguro la comparacion de abajo)
                        size2buy = 0
                    if not size2sell:
                        size2sell = 0
                    if not size2last:
                        size2last = 0
                    size2buy = float(size2buy)
                    size2sell = float(size2sell)
                    size2last = float(size2last)
                    
                '''
                if allReady == False:
                    price2sell = None
                    price2buy = None
                    price2last = None
                    size2buy = None
                    size2sell = None
                    size2last = None
                '''
                bUpdated = False
                if allReady != False:
                    
                    price2buy = round (price2buy, 5)
                    price2sell = round (price2sell, 5)
                    price2last = round (price2last, 5)
                    data_args = {}
                    if contrato['currentPrices']['BUY'] != price2buy and size2buy > 0:
                        contrato['currentPrices']['BUY'] = price2buy
                        contrato['currentPrices']['updated'] = True
                        data_args['ASK'] = price2buy
                        bUpdated = True
                    if contrato['currentPrices']['SELL'] != price2sell and size2sell > 0:
                        contrato['currentPrices']['SELL'] = price2sell
                        contrato['currentPrices']['updated'] = True
                        data_args['BID'] = price2sell
                        bUpdated = True
                    if contrato['currentPrices']['LAST'] != price2last and size2last > 0:
                        contrato['currentPrices']['LAST'] = price2last
                        contrato['currentPrices']['updated'] = True
                        data_args['LAST'] = price2last
                        bUpdated = True
                    if contrato['currentPrices']['BUY_SIZE'] != size2buy and size2buy > 0:
                        contrato['currentPrices']['BUY_SIZE'] = size2buy
                        contrato['currentPrices']['updated'] = True
                        data_args['ASK_SIZE'] = size2buy
                        bUpdated = True
                    if contrato['currentPrices']['SELL_SIZE'] != size2sell and size2sell > 0:
                        contrato['currentPrices']['SELL_SIZE'] = size2sell
                        contrato['currentPrices']['updated'] = True
                        data_args['BID_SIZE'] = size2sell
                        bUpdated = True
                    if contrato['currentPrices']['LAST_SIZE'] != size2last and size2last > 0:
                        contrato['currentPrices']['LAST_SIZE'] = size2last
                        contrato['currentPrices']['updated'] = True
                        data_args['LAST_SIZE'] = size2last
                        bUpdated = True

                    # Se actualiza la DB para el contrato['gConId'] con estos datos:
                    if bUpdated:
                        contrato['dbPandas'].dbUpdateAddPrices(data_args)  # no estariamos aquí si no hay 'dbpandas'

    def contractUpdatePnL(self, reqIdPnL):
        # Tenemos por un lado los contratos BAG
        #  y luego hay que actualizar los legs por si alguno tiene este reqId
        # Los que no son BAG tambien tienren el contractReqIdLegs con 1 solo entry, por lo que se buscan los dos igual
        # reqIdPnL ['11'] ---> {11: {'dailyPnL':dailyPnL, 'unrealizedPnL':unrealizedPnL, 'realizedPnL':realizedPnL, 'pos': pos, 'value':value}}

        for gConId, contrato in self.contractDict_.items():
            updated = False
            for conReqLeg in contrato['contractReqIdLegs']:  # Directamente esto implica que contrato['hasContractSymbols'] = True
                if ('reqIdPnL' in conReqLeg) and (conReqLeg['reqIdPnL'] == reqIdPnL):
                    updated = True
            if updated:
                dailyPnL = 0
                unrealizedPnL = 0
                realizedPnL =  0
                value = 0

                allReady = True

                for conReqLeg in contrato['contractReqIdLegs']:       
                    if conReqLeg['reqIdPnL'] == None:
                        allReady = False            # No todos los legs estan subscritos
                        break
                    legReqId = conReqLeg['reqIdPnL']
                    if not legReqId in self.pnl_:   # Está subscrito pero no hemos recibido el PnL de este leg aun
                        allReady = False
                        break

                    if dailyPnL != None:   # Si es None es que no están todos
                        if not 'dailyPnL' in self.pnl_[legReqId]:  
                            dailyPnL = None   
                        else:
                            dailyPnL += self.pnl_[legReqId]['dailyPnL']

                    if realizedPnL != None:   # Si es None es que no están todos
                        if not 'realizedPnL' in self.pnl_[legReqId]:  
                            realizedPnL = None   
                        else:
                            realizedPnL += self.pnl_[legReqId]['realizedPnL']

                    if unrealizedPnL != None:   # Si es None es que no están todos
                        if not 'unrealizedPnL' in self.pnl_[legReqId]:  
                            unrealizedPnL = None   
                        else:
                            unrealizedPnL += self.pnl_[legReqId]['unrealizedPnL']

                    if value != None:   # Si es None es que no están todos
                        if not 'value' in self.pnl_[legReqId]:  
                            value = None   
                        else:
                            value += self.pnl_[legReqId]['value']

                if allReady != False:
                    bUpdated = False
                    if contrato['pnl']['dailyPnL'] != dailyPnL and dailyPnL != None:
                        contrato['pnl']['dailyPnL'] = dailyPnL
                        contrato['pnl']['updated'] = True
                        bUpdated = True
                    if contrato['pnl']['realizedPnL'] != realizedPnL and realizedPnL != None:
                        contrato['pnl']['realizedPnL'] = realizedPnL
                        contrato['pnl']['updated'] = True
                        bUpdated = True
                    if contrato['pnl']['unrealizedPnL'] != unrealizedPnL and unrealizedPnL != None:
                        contrato['pnl']['unrealizedPnL'] = unrealizedPnL
                        contrato['pnl']['updated'] = True
                        bUpdated = True
                    if contrato['pnl']['value'] != value and value != None:
                        contrato['pnl']['value'] = value
                        contrato['pnl']['updated'] = True
                        bUpdated = True

                    # Se actualiza la DB para el contrato['gConId'] con estos datos:
                    if bUpdated:
                        lSymbol = contrato['fullSymbol']
                        
                        data_args = {'dailyPnL': contrato['pnl']['dailyPnL'], 
                                     'realizedPnL':contrato['pnl']['realizedPnL'], 
                                     'unrealizedPnL':contrato['pnl']['unrealizedPnL']
                                     }
                        if self.strategies_.strategyGetStrategyTypesBySymbol(lSymbol) != None:   # Solo añado a la DB si forma parte de una strategia
                            contrato['dbPandas'].dbUpdateAddPnL(data_args) # Si estamos aqui es que hay dbPandas
                   

    def contractGetCurrentPricesPerGconId (self, gConId):
        if gConId in self.contractDict_:
            return self.contractDict_[gConId]['currentPrices']
        else:
            return None

    def contractCheckIfExists (self, gConId):
        return gConId in self.contractDict_

    def contractGetContractbyGconId (self, gConId):
        if gConId in self.contractDict_:
            return self.contractDict_[gConId]
        else:
            logging.info ('No he encontrado el contrato con gConId: %s', gConId)
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
        for gConId, contrato in self.contractDict_.items():
            if ('fullSymbol' in contrato) and contrato['fullSymbol'] == symbol:
                return contrato
        return None

    def contractSubscribeTickPrice(self, contractReqIdLeg): 
        # contrato['contractReqIdLegs'] --> [{'conId': , 'reqId': None, 'ratio': , 'action': , 'lSymbol': },...]
        # El contractReqIdLeg es un leg de un contrato. Puede que coincida con el de otro, por ejemplo:
        #   Contrato HEV2-HEZ2 tiene dos legs, y cada una de ellas va a coindir con el del contrato HEV2 y HEZ2

        # Busco a ver si hay un contrato con un leg igual que ya tenga reqId:
        for gConId, contratoTemp in self.contractDict_.items():
            for contractReqIdLegTemp in contratoTemp['contractReqIdLegs']:
                if (contractReqIdLegTemp['conId'] == contractReqIdLeg['conId']) and contractReqIdLegTemp['reqId'] != None:
                    return contractReqIdLegTemp['reqId']
        # Si no hay ninguno, tengo que crear la subscripcion
        # Para el reqMktData el Contract tiene que ser virgen sin conid
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

    def contractSubscribePnL(self, contractReqIdLeg): 
        # contrato['contractReqIdLegs'] --> [{'conId': , 'reqId': None, 'reqIdPnL': None, 'ratio': , 'action': , 'lSymbol': },...]
        # El contractReqIdLeg es un leg de un contrato. Puede que coincida con el de otro, por ejemplo:
        #   Contrato HEV2-HEZ2 tiene dos legs, y cada una de ellas va a coindir con el del contrato HEV2 y HEZ2

        # Busco a ver si hay un contrato con un leg igual que ya tenga reqId:
        for gConId, contratoTemp in self.contractDict_.items():
            for contractReqIdLegTemp in contratoTemp['contractReqIdLegs']:
                if (contractReqIdLegTemp['conId'] == contractReqIdLeg['conId']):
                    if 'reqIdPnL' in contractReqIdLegTemp and contractReqIdLegTemp['reqIdPnL'] != None:
                        return contractReqIdLegTemp['reqIdPnL']
        # Si no hay ninguno, tengo que crear la subscripcion

        accountId = self.accountData_['accountId']

        reqId = self.appObj_.reqPnLSingle (accountId, contractReqIdLeg['conId'])
        contractReqIdLeg['reqIdPnL'] = reqId
        return reqId

    def contractGetSymbolsIfFullLegsDataByGconId (self, gConId):
        simbolos = []
        simbolo = {}

        if (gConId in self.contractDict_) and self.contractDict_[gConId]['fullLegData']:
            contrato = self.contractDict_[gConId]
            if contrato['contract'].secType == "BAG":
                for leg in contrato['contract'].comboLegs:
                    if leg.conId in self.contractDict_:
                        contratoLeg = self.contractDict_[leg.conId]
                        simbolo = {'conId': contratoLeg['contract'].conId, 'reqId': None, 'ratio': leg.ratio, 'action': leg.action, 'lSymbol': contratoLeg['contract'].localSymbol}
                        simbolos.append(simbolo)
                        exists = True
                    else:  # Si alguno no existe, devolvemos lista vacia
                        simbolos = []
                        return simbolos
            else:
                simbolo = {'conId': contrato['contract'].conId, 'reqId': None, 'ratio': 1, 'action': 'BUY', 'lSymbol': contrato['contract'].localSymbol}
                simbolos.append(simbolo)
        return simbolos


    def contractSummaryAllFull (self):
        summaryStr = ''
        for gConId in self.contractDict_:
            summaryStr += self.contractSummaryFull (gConId)
        return summaryStr

    def contractSummaryAllBrief (self):
        summaryStr = ''
        for gConId in self.contractDict_:
            summaryStr += self.contractSummaryBrief (gConId)

        return summaryStr

    def contractSummaryAllBriefWithPrice (self):
        summaryStr = ''
        for gConId in self.contractDict_:
            logging.debug ('gConID: %s',  str(gConId))
            summaryStr += '[' + str(gConId) + '] - '
            summaryStr += self.contractSummaryBriefWithPrice (gConId)
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
        
        if gConId in self.contractDict_:
            contrato = self.contractDict_[gConId]
        else:
            return summaryStr

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
        return summaryStr
                
    def contractSummaryBrief (self, gConId):
        result = True
        summaryStr = ''
        if gConId in self.contractDict_:
            contrato = self.contractDict_[gConId]
        else:
            return summaryStr

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
        
        return summaryStr
        
    def legSummary (self, leg, symbol):
        result = True
        exists = False
        summaryStr = ''
        
        
        contrato1 = Contract() 
        if leg.conId in self.contractDict_:
            contrato1 = self.contractDict_[leg.conId]['contract']
            exists = True
    
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
        if leg.conId in self.contractDict_:
            contrato1 = self.contractDict_[leg.conId]['contract']
            exists = True

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
        orden['Executed'] = False
        orden['toPrint'] = False
        orden['toCancel'] = False
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
                bChanged = False
                bStatusChanged = False
                if not contractObj=="" and contractObj != None:
                    orden['contractId'] = self.contractGetGconId(contractObj)
                if not orderObj=="" and orderObj != None:
                    orden['order'] = orderObj
                if not paramsDict=="" and paramsDict != None:
                    #Comprobar si ha cambiado algo
                    if orden['params'] != None:
                        if 'status' in orden['params'] and 'status' in paramsDict and orden['params']['status'] != paramsDict['status']:
                            bChanged = True
                        elif 'status' not in orden['params'] and 'status' in paramsDict:
                            bChanged = True
                        if 'filled' in orden['params'] and 'filled' in paramsDict and orden['params']['filled'] != paramsDict['filled']:
                            bChanged = True
                        elif 'filled' not in orden['params'] and 'filled' in paramsDict:
                            bChanged = True
                        if 'remaining' in orden['params'] and 'remaining' in paramsDict and orden['params']['remaining'] != paramsDict['remaining']:
                            bChanged = True
                        elif 'remaining' not in orden['params'] and 'remaining' in paramsDict:
                            bChanged = True
                        if 'lastFillPrice' in orden['params'] and 'lastFillPrice' in paramsDict and orden['params']['lastFillPrice'] != paramsDict['lastFillPrice']:
                            bChanged = True
                    elif 'status' in paramsDict or 'filled' in paramsDict or 'remaining' in paramsDict:
                        bChanged = True
                    orden['params'].update(paramsDict)
                orden['toPrint'] = True
                str_o = self.orderSummary(orden)
                if bChanged:
                    logging.info (str_o)
                else:
                    logging.debug (str_o)

                self.orderCheckIfRemove(orden)

                break
                
        if not exists:
            result = self.orderAdd (contractObj, orderObj, paramsDict)

        return (result)

    def orderReturnListAll(self):
        return self.orderList_
    
    def orderCheckIfRemove (self, orden):
        # Despues de un update, mirar si hay que borrarla
        return
        if 'status' in orden['params']:
            if orden['params']['status'] == 'Cancelled':
                self.orderList_.remove(orden)
            if orden['params']['status'] == 'Filled':
                self.orderList_.remove(orden)

    def orderSetExecutedStatus (self, orderId, bExec):
        for orden in self.orderList_: 
            if orden['order'].orderId == orderId:
                orden['Executed'] = bExec
                return True
        return None

    def orderGetStatusbyOrderId (self, orderId):
        if not orderId:
            return None
        for orden in self.orderList_: 
            if orden['order'].orderId == orderId:
                if 'status' in orden['params']:
                    return orden['params']['status']
                break
        return None

    def orderGetStatusbyOrderPermId (self, orderPermId):
        if orderPermId == None:
            return None
        for orden in self.orderList_: 
            if int(orden['permId']) == int(orderPermId):
                if 'status' in orden['params']:
                    return orden['params']['status']
                break
        return None

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
        return None

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
        if orderPermId == None:
            return False
        for order in self.orderList_: 
            if int(order['permId']) == int(orderPermId):
                return True
        return False

    def orderCheckIfExistsByOrderId (self, orderId):
        if not orderId:
            return False
        for order in self.orderList_: 
            if int(order['order'].orderId) == int(orderId):
                return True
        return False

    def orderPlaceBrief (self, symbol, secType, action, oType, lmtPrice, qty):
        newreqDownId = self.appObj_.placeOrderBrief (symbol, secType, action, oType, lmtPrice, qty) 
        return newreqDownId

    def orderPlaceBracket (self, symbol, secType, action, qty, lmtPrice, takeProfitLimitPrice, stopLossPrice):
        ordersIds = self.appObj_.placeBracketOrder (symbol, secType, action, qty, lmtPrice, takeProfitLimitPrice, stopLossPrice) 
        return ordersIds

    def orderPlaceOCA (self, symbol, secType, actionUp, actionDown, qty, LmtUp, LmtDown):
        ordersIds = self.appObj_.placeOCAOrder (symbol, secType, actionUp, actionDown, qty, LmtUp, LmtDown) 
        return ordersIds

    def orderCancelByOrderId (self, orderId):
        for order in self.orderList_: 
            if int(order['order'].orderId) == int(orderId):
                order['toCancel'] = True
                self.appObj_.cancelOrderByOrderId (orderId)
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

        #orden['toPrint'] = False

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

        #orden['toPrint'] = False
                
        return summaryStr
                
 
