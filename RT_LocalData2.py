#from typing_extensions import Self
from ibapi.contract import *
from ibapi.order import *
from ibapi.utils import floatMaxString, longMaxString
from ibapi.common import UNSET_INTEGER, UNSET_DOUBLE, UNSET_LONG, UNSET_DECIMAL, DOUBLE_INFINITY, INFINITY_STR
#import strategiesNew
import pandasDB
import logging
import datetime
import influxAPI
import utils
import tools.yfinance_grab as yf

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
        self.strategies_ = None # Se inicializa desde Local_Daemon llamando al constructor dr Strategies, y ese lo copia aqui
        self.influxIC_ = influxAPI.InfluxClient()

        self.accountData_ = {}
        self.accountPandas_ = None
        self.accountInit_ = False
        self.orderList_ = []  # includes orders and contracts (hay que sacar los contracts a puntero externo, y los usan las posiciones)
        self.contractDict_ = {}  # Directamente dict de contracts

        self.tickPrices_ = {}    # Key: reqId ['12'] ---> {12: {'BID': 10, 'ASK': 10.1, 'LAST': 10.1, 'HIGH': 11, 'LOW': 9, 'OPEN':10.5, 'CLOSE': 10.2}}
        self.pnl_ = {}

        self.contractInconplete_ = False

        self.dataFeed = True


    ########################################
    # Data feed

    # Si es false quiere decir que no recibo datos
    # Tendría que cargar de db

    def dataFeedSetState (self, state):
        if state == False or state == True:
            self.dataFeed = state
        else:
            return

        if state == False:
            logging.error ("")
            logging.error ("Estamos en conflicto con la sesion LIVE")
            logging.error ("")

    def dataFeedGetState (self):
        return self.dataFeed
    

    ########################################
    # Executions

    # Deberíamos tener un Pandas+CSV que guarde todas las execs.
    # Si se pierde la conexsión habría que pedir todas y comparar

    def executionAnalisys (self, data):
        #Podemos hacer más cosas, de momento solo informamos a las estrategias
        self.orderAddExecData(data)

    def commissionAnalisys (self, data):
        #Podemos hacer más cosas, de momento solo informamos a las estrategias
        self.orderAddCommissionData (data)

    ########################################
    # Account

    def accountTagUpdate (self, data):

        keys_account = [
            'accountId', 'Cushion', 'LookAheadNextChange', 'AccruedCash', 
            'AvailableFunds', 'BuyingPower', 'EquityWithLoanValue', 'ExcessLiquidity', 'FullAvailableFunds',
            'FullExcessLiquidity','FullInitMarginReq','FullMaintMarginReq','GrossPositionValue','InitMarginReq',
            'LookAheadAvailableFunds','LookAheadExcessLiquidity','LookAheadInitMarginReq','LookAheadMaintMarginReq',
            'MaintMarginReq','NetLiquidation','TotalCashValue'
        ]

        if self.accountPandas_ == None and 'accountId' in self.accountData_: 
            self.accountPandas_ = pandasDB.dbPandasAccount (self.accountData_['accountId'], self.influxIC_) 

        updated = False
        if 'end' in data:
            logging.debug ("Tipo de account info: End")
        if 'reqId' in data:
            logging.debug ("Tipo de account info: Summary")
        if 'currency' in data:
            logging.debug ("Tipo de account info: Update")


        #reqId = data['reqId']
        if ('end' not in data):
            account = data['account']
            tag = data['tag']
            value = data['value']

            if tag in keys_account:
                updated = True
                dictLocal = {}
                dictLocal[tag] = value
                dictLocal['accountId'] = account
                self.accountData_.update (dictLocal)
                logging.debug ("Escribo la account info:\n%s", dictLocal)
        else:
            if not self.accountInit_:
                logging.debug ("Escribo la account info:\n%s", self.accountSummary())
            self.accountInit_ = True
            
        if ('end' in data) or ('currency' in data and self.accountInit_ == True and updated == True):
            self.accountPandas_.dbUpdateAddAccountData (self.accountData_)
        if ('end' in data):
            # Como ya hemos recibido todo, disparo la subscripcion 
            self.appObj_.reqAccountUpdates(True, self.accountData_['accountId'])


    def accountSummary (self):
        summaryStr = ''
        for tag in self.accountData_:
            summaryStr += str(tag) + ": " + str(self.accountData_[tag]) + '\n'
        return summaryStr

    ########################################
    # Positions


      
    def positionUpdate (self, data):
        posEnd = data['positionEnd']
        if posEnd:
            self.postionFixSpreads()
            return
        
        result = True
        contractObj = data['contract']
        nPosition = data['position']
        avgCost = data['avgCost']

        if not contractObj == "":
            #print ('Actualizo cont')
            ret = self.contractAdd (contractObj)

        gConId = self.contractGetGconId(contractObj)

        logging.info("[Posicion] Actualizada %s: %d", contractObj.localSymbol, nPosition)

        lotes_contrato = utils.getLotesContratoBySymbol (contractObj.localSymbol)

        # self.contractDict_[gConId]['pos'] = nPosition  # Solo haría falta esto cuando lo pase todo.
        self.contractDict_[gConId]['pos_total'] = nPosition  # Solo haría falta esto cuando lo pase todo.
        self.contractDict_[gConId]['posAvgPrice'] = avgCost/lotes_contrato

        return (result)

    def postionFixSpreads (self):
        lenght_list = []
        # Voy a generar una lista de las longitudes de contrato que tengo.
        # Sirve para evaluar primero las mas largas
        for gConId, contrato in self.contractDict_.items():
            symbol = self.contractSummaryBrief(gConId)
            cl = utils.contractCode2list(symbol)
            try:
                cl_l = len(cl)
            except:
                cl_l = 1
            lenght_list.append(cl_l)
            contrato['pos'] = contrato['pos_total']   # Reseteo las posiciones

        lenght_list.sort(reverse=True)
        lenght_list = list(dict.fromkeys(lenght_list))  # sirve para quitar dupps

        for lenth in lenght_list:    # esto es para que se hagan en orden, las mas largas primero
            for gConId, contrato in self.contractDict_.items():
                #Repaso todas la bags para ver si cada contrato individual tiene posiciones
                symbol = self.contractSummaryBrief(gConId)
                cl = utils.contractCode2list(symbol)
                try:
                    cl_l = len(cl)
                except:
                    cl_l = 1
                if contrato['contract'].secType == "BAG" and cl_l == lenth:
                    self.positionFixSpreadsIntra(contrato)
                


    def positionFixSpreadsIntra (self, contrato):
        pos_min = None
        # Busco las posiciones mínimas que tienen todos los legs.
        # Hay que comprobar que son todas en el mismo sentodo (con la correcccion del ratio)
        # contractReqIdLegs: Lista de dicts: [{'conId': , 'reqId': None, 'reqIdPnL': None, 'ratio': , 'action':, 'lSymbol':  },...]
        logging.info("Compruebo BAG %s", contrato['fullSymbol'])

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
            logging.info("      %s: %d(%d)", contractLegInfo['lSymbol'], currPosLeg, pos_min)
        # pos_min es las que tengo que robar (multiplicado por el ratio de cada uno) a cada conId, para darselo al BAG
        
        logging.info("[Posicion] Actualizo BAG %s con esta position: %d", contrato['fullSymbol'], pos_min)
        avgPrice = 0.0
        for contractLegInfo in contrato['contractReqIdLegs']:
            conId = contractLegInfo['conId']
            ratio = contractLegInfo['ratio']
        
            if contractLegInfo['action'] == 'SELL':
                ratio = (-1) * ratio # Normalizando a siempre positivo (BUY) o siempre negativo (SELL)

            avgPrice += self.contractDict_[conId]['posAvgPrice'] * ratio

            deltaPos = pos_min * ratio
            logging.info("      %s: %d", contractLegInfo['lSymbol'], deltaPos)
            try:
                self.contractDict_[conId]['pos'] -= int(deltaPos)
            except:
                logging.error("      Problema con el self.contractDict_[conId]['pos'] de %s y la nueva %d", contractLegInfo['lSymbol'], deltaPos)
            
            
            if self.contractDict_[conId]['pos'] == 0:
                self.contractDict_[conId]['posAvgPrice'] = 0.0
        
        #Finalmente, pongo pos_min al BAG
        if contrato['pos'] == None: # Inicializamos
            contrato['pos'] = 0
        contrato['pos'] = int(pos_min)
        contrato['posAvgPrice'] = avgPrice

    def positionDeleteAll (self):
        # Pasar por contracts y borrar posiciones
        for gConId, contrato in self.contractDict_.items():
            contrato['pos'] = None
            contrato['posAvgPrice'] = 0.0

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
            bChange_volume = False
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
                if not 'VOLUME' in prices or ('VOLUME' in prices and prices['VOLUME'] != size):
                    bChange_volume = True
                    logging.debug ('Hemos recibido Volume (req:%s): %s', reqId, size)
                    prices['VOLUME'] = size

            self.tickPrices_[reqId] = prices
        
            if bChange:  # Solo con size
                logging.debug("Deberia actualizar valor")
                self.contractUpdateTicks(reqId)

            if bChange_volume:
                logging.debug("Deberia actualizar valor")
                self.contractUpdateVolumeTicks(reqId)

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
            return gConId

        contrato = {}
        contrato['gConId'] = gConId
        contrato['fullSymbol'] = None
        contrato['contract'] = contractObj
        contrato['pos'] = None         # En esta tengo las que presento en pantalla normalizadas (quitando las quw van a bags)
        contrato['pos_total'] = None   # Aqui están todas tal cual viene de ib
        contrato['posAvgPrice'] = 0.0
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
        contrato['VOLUME'] = None
        contrato['pnl'] = {}
        contrato['pnl']['dailyPnL'] = None
        contrato['pnl']['unrealizedPnL'] = None
        contrato['pnl']['realizedPnL'] = None
        contrato['pnl']['value'] = None
        contrato['hasContractSymbols'] = False
        contrato['semaforoYfinance'] = False
        contrato['contratoIndirecto'] = True

        self.contractDict_[gConId] = contrato    

        return gConId

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
                            gConId = self.contractAdd(contrato1)
                            

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
        try:
            file1 = open('strategies/ContractsWatchList.conf', 'r')
        except:
            logging.error ('Fichero ContractsWatchList.conf no existe')
            return

        Lines = file1.readlines()
  
        for line in Lines:
            if line.rstrip() == '':
                continue
            contractN = self.appObj_.contractFUTcreate(line.rstrip())
            gConId = self.contractAdd(contractN)
            self.contractIndirectoSet (gConId, False)



    def contractWriteFixedWatchlist (self, contractList):
        error = False
        with open('strategies/ContractsWatchList.conf', 'w') as f:
            for line in contractList:
                symbol = line.rstrip()
                f.writelines(line + '\n')
                contract = self.contractGetBySymbol(symbol)
                if contract == None:
                    logging.info ('En la watchlist hay un contrato con simbolo %s que no existe. Lo creamos.', symbol)
                    contractN = self.appObj_.contractFUTcreate(symbol)
                    if not contractN:
                        logging.error ('Error creando el contrato %s. No se puede añadir', symbol)
                        error = True
                    gConId = self.contractAdd(contractN)
                    self.contractIndirectoSet (gConId, False)
        return not error

    def contractReturnFixedWatchlist (self):
        contractList = []
        try:
            file1 = open('strategies/ContractsWatchList.conf', 'r')
        except:
            return contractList
        
        Lines = file1.readlines()
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
            lastPnL = contrato['dbPandas'].dbGetLastPnL()
            logging.info ('    dailyPnL: %s', lastPnL['dailyPnL'])
            contrato['pnl']['dailyPnL'] = lastPnL['dailyPnL']
            contrato['pnl']['unrealizedPnL'] = lastPnL['unrealizedPnL']
            contrato['pnl']['realizedPnL'] = lastPnL['realizedPnL']


    def contractGetListUnique(self):
        contratos = []
        for gConId, contrato in self.contractDict_.items():
            contratos.append(contrato['fullSymbol'])
        return contratos

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
                lsymbol = contrato['fullSymbol']
                logging.debug ('Tick (req:%s): %s', reqId, lsymbol)
                price2sell = 0.0
                price2buy = 0.0
                price2last = 0.0
                size2sell = None
                size2buy = None
                size2last = None
                volumen = None
                allReady = True
                for conReqLeg in contrato['contractReqIdLegs']:      
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
                    
                bUpdated = False
                if allReady != False:
                    
                    price2buy = round (price2buy, 5)
                    price2sell = round (price2sell, 5)
                    price2last = round (price2last, 5)
                    data_args = {}
                    if contrato['currentPrices']['BUY'] != price2buy and size2buy > 0:
                        contrato['currentPrices']['BUY'] = price2buy
                        data_args['ASK'] = price2buy
                        bUpdated = True
                    if contrato['currentPrices']['SELL'] != price2sell and size2sell > 0:
                        contrato['currentPrices']['SELL'] = price2sell
                        data_args['BID'] = price2sell
                        bUpdated = True
                    if contrato['currentPrices']['LAST'] != price2last and size2last > 0:
                        contrato['currentPrices']['LAST'] = price2last
                        data_args['LAST'] = price2last
                        bUpdated = True
                    if contrato['currentPrices']['BUY_SIZE'] != size2buy and size2buy > 0:
                        contrato['currentPrices']['BUY_SIZE'] = size2buy
                        data_args['ASK_SIZE'] = size2buy
                        bUpdated = True
                    if contrato['currentPrices']['SELL_SIZE'] != size2sell and size2sell > 0:
                        contrato['currentPrices']['SELL_SIZE'] = size2sell
                        data_args['BID_SIZE'] = size2sell
                        bUpdated = True
                    if contrato['currentPrices']['LAST_SIZE'] != size2last and size2last > 0:
                        contrato['currentPrices']['LAST_SIZE'] = size2last
                        data_args['LAST_SIZE'] = size2last
                        bUpdated = True

                    # Se actualiza la DB para el contrato['gConId'] con estos datos:
                    if bUpdated:
                        contrato['dbPandas'].dbUpdateAddPrices(data_args)  # no estariamos aquí si no hay 'dbpandas'

    def contractUpdateVolumeTicks(self, reqId):
        # Tenemos por un lado los contratos BAG
        #  y luego hay que actualizar los legs por si alguno tiene este reqId
        # Los que no son BAG tambien tienren el contractReqIdLegs con 1 solo entry, por lo que se buscan los dos igual
        for gConId, contrato in self.contractDict_.items():
            updated = False
            for conReqLeg in contrato['contractReqIdLegs']: # Directamente esto implica que contrato['hasContractSymbols'] = True
                if conReqLeg['reqId'] == reqId:
                    updated = True
            if updated:
                lsymbol = contrato['fullSymbol']
                nLegs = len(contrato['contractReqIdLegs'])
                logging.debug('El contrato %s: ha actualizado volumen. Vamoso a reviar sus legs (%s)', lsymbol, nLegs)
                logging.debug ('Tick (req:%s): %s', reqId, lsymbol)
                volumen = None
                allReadyVolumen = True
                for conReqLeg in contrato['contractReqIdLegs']:      
                    if conReqLeg['reqId'] == None:
                        allReadyVolumen = False
                        break
                    legReqId = conReqLeg['reqId']
                    if not legReqId in self.tickPrices_:
                        allReadyVolumen = False
                        break
                    if not 'VOLUME' in self.tickPrices_[legReqId]:  
                        allReadyVolumen = False
                        break

                    logging.debug('    Revisamos un leg: %s', conReqLeg['lSymbol'])
                    logging.debug('       Volume: %s. New one: %s', volumen, int(self.tickPrices_[legReqId]['VOLUME']))
                    if volumen == None:
                        volumen = int(self.tickPrices_[legReqId]['VOLUME'])
                    else:
                        volumen = min(volumen, int(self.tickPrices_[legReqId]['VOLUME']))

                if allReadyVolumen != False:
                    data_args = {}
                    if contrato['VOLUME'] != volumen:
                        contrato['VOLUME'] = volumen
                        data_args['VOLUME'] = volumen
                        logging.debug('    Volumen final de %s: %s', lsymbol, volumen)
                        contrato['dbPandas'].dbUpdateAddVolume(data_args)




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
                dailyPnL = 0.0
                unrealizedPnL = 0.0
                realizedPnL =  0
                value = 0.0

                allReady = True

                logging.debug ('-------------------------------------')
                logging.debug ('Analizo: %s', contrato['fullSymbol'])

                for conReqLeg in contrato['contractReqIdLegs']:  
                    #conReqLeg = {'conId': , 'reqId': None, 'reqIdPnL':None, 'ratio': leg.ratio, 'action': leg.action, 'lSymbol': contratoLeg['contract'].localSymbol}
                    if conReqLeg['reqIdPnL'] == None:
                        allReady = False            # No todos los legs estan subscritos
                        break
                    legReqId = conReqLeg['reqIdPnL']
                    if not legReqId in self.pnl_:   # Está subscrito pero no hemos recibido el PnL de este leg aun
                        allReady = False
                        break

                    # Esto lo hago para ponderar el peso de cada PnL segun las posiciones reales

                    logging.debug ('Pnl self.pnl_: %s', self.pnl_[legReqId])
                    logging.debug ('Pnl conReqLeg: %s', conReqLeg)

                    pos_total_leg = float(abs(self.contractDict_[conReqLeg['conId']]['pos_total']))
                    logging.debug ('   Pos Total: %s', pos_total_leg)
                    pos_este_contrato = int(abs(contrato['pos']))
                    logging.debug ('   Pos Local: %s', pos_este_contrato)

                    if dailyPnL != None:   # Si es None es que no están todos
                        if not 'dailyPnL' in self.pnl_[legReqId]:  
                            dailyPnL = None   
                        else:
                            leg_dailyPnL = self.pnl_[legReqId]['dailyPnL']
                            if pos_total_leg != 0:
                                leg_dailyPnL = leg_dailyPnL / pos_total_leg * abs(conReqLeg['ratio'])
                            else:
                                leg_dailyPnL = 0
                            dailyPnL += leg_dailyPnL * pos_este_contrato

                    if realizedPnL != None:   # Si es None es que no están todos
                        if not 'realizedPnL' in self.pnl_[legReqId]:  
                            realizedPnL = None   
                        else:
                            leg_realizedPnL = self.pnl_[legReqId]['realizedPnL']
                            if pos_total_leg != 0:
                                leg_realizedPnL = leg_realizedPnL / pos_total_leg * abs(conReqLeg['ratio'])
                            else:
                                leg_realizedPnL = 0
                            realizedPnL += leg_realizedPnL * pos_este_contrato

                    if unrealizedPnL != None:   # Si es None es que no están todos
                        if not 'unrealizedPnL' in self.pnl_[legReqId]:  
                            unrealizedPnL = None   
                        else:
                            leg_unrealizedPnL = self.pnl_[legReqId]['unrealizedPnL']
                            if pos_total_leg != 0:
                                leg_unrealizedPnL = leg_unrealizedPnL / pos_total_leg * abs(conReqLeg['ratio'])
                            else:
                                leg_unrealizedPnL = 0
                            unrealizedPnL += leg_unrealizedPnL * pos_este_contrato
                            
                    if value != None:   # Si es None es que no están todos
                        if not 'value' in self.pnl_[legReqId]:  
                            value = None   
                        else:
                            leg_valuePnL = self.pnl_[legReqId]['value']
                            if pos_total_leg != 0:
                                leg_valuePnL = leg_valuePnL / pos_total_leg * abs(conReqLeg['ratio'])
                            else:
                                leg_valuePnL = 0
                            value += leg_valuePnL * pos_este_contrato

                logging.debug ('pos:%s', contrato['pos'])
                logging.debug ('dailyPnL:%s', dailyPnL)
                logging.debug ('realizedPnL:%s', realizedPnL)
                logging.debug ('unrealizedPnL:%s', unrealizedPnL)
                logging.debug ('value:%s', value)

                if allReady != False:
                    bUpdated = False
                    if contrato['pnl']['dailyPnL'] != dailyPnL and dailyPnL != None:
                        contrato['pnl']['dailyPnL'] = dailyPnL
                        bUpdated = True
                    if contrato['pnl']['realizedPnL'] != realizedPnL and realizedPnL != None:
                        contrato['pnl']['realizedPnL'] = realizedPnL
                        bUpdated = True
                    if contrato['pnl']['unrealizedPnL'] != unrealizedPnL and unrealizedPnL != None:
                        contrato['pnl']['unrealizedPnL'] = unrealizedPnL
                        bUpdated = True
                    if contrato['pnl']['value'] != value and value != None:
                        contrato['pnl']['value'] = value
                        bUpdated = True

                    # Se actualiza la DB para el contrato['gConId'] con estos datos:
                    if bUpdated:
                        lSymbol = contrato['fullSymbol']
                        
                        data_args = {'dailyPnL': contrato['pnl']['dailyPnL'], 
                                     'realizedPnL':contrato['pnl']['realizedPnL'], 
                                     'unrealizedPnL':contrato['pnl']['unrealizedPnL']
                                     }
                        logging.debug ('Actualizo %s con: %s', contrato['fullSymbol'], data_args)
                        if self.strategies_.strategyGetStrategyTypesBySymbol(lSymbol) != None:   # Solo añado a la DB si forma parte de una strategia
                            contrato['dbPandas'].dbUpdateAddPnL(data_args) # Si estamos aqui es que hay dbPandas
                   

    def contractGetCurrentPricesPerGconId (self, gConId):
        if gConId in self.contractDict_:
            return self.contractDict_[gConId]['currentPrices']
        else:
            return None

    def contractCheckIfExists (self, gConId):
        return gConId in self.contractDict_

    def contractIndirectoSet (self, gConId, indirecto):
        if gConId in self.contractDict_:
            self.contractDict_[gConId]['contratoIndirecto'] = indirecto

    def contractIndirectoGet (self, gConId):
        if gConId in self.contractDict_:
            return self.contractDict_[gConId]['contratoIndirecto']

    def contractGetContractbyGconId (self, gConId):
        try:
            gConId = int(gConId)
        except:
            logging.error ('Error en gCondId: [%s]', gConId)
            return None

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



    def contractYFinanceExpand(self, gConId):

        contrato = self.contractGetContractbyGconId (gConId)

        if not contrato:
            logging.error ('El gCondId [%s] no existe', gConId)
            return None

        symbol = contrato['fullSymbol']

        if contrato['semaforoYfinance']:
            logging.error ('Ya estamos descargando los datos de este contrato: %s', symbol)
            return

        firstDate = contrato['dbPandas'].dbGetFirstCompDate()
        logging.info('Sacamos yFinance de Contrato [%s] desde [%s]', symbol, firstDate)
        contrato['semaforoYfinance'] = True
        data_df, vol_series = yf.yfinanceGetDelta1h (symbol, firstDate)

        for cont_data in data_df:
            contrato_l = self.contractGetBySymbol (cont_data)
            if not contrato_l:
                logging.error ('No he encontrado el contrato para symbol %s', cont_data)
                continue
            contrato_l['dbPandas'].dbAddCompDataFrame (data_df[cont_data])
            contrato_l['dbPandas'].dbAddVolDataFrame (vol_series[cont_data])

        contrato['semaforoYfinance'] = False
        return True

    def contractCompDataSave(self, gConId):
        
        contrato = self.contractGetContractbyGconId (gConId)

        if not contrato:
            logging.error ('El gCondId [%s] no existe', gConId)
            return None

        symbol = contrato['fullSymbol']

        contrato['dbPandas'].dbUpdateInfluxCompVolPrices()

    def contractReloadCompPrices (self):
        for gConId, contrato in self.contractDict_.items():
            contrato['dbPandas'].dbReadInfluxPricesComp()

    def contractReloadPrices (self):
        for gConId, contrato in self.contractDict_.items():
            contrato['dbPandas'].dbReadInfluxPrices()

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

        if paramsDict == None:
            paramsDict = {}

        
        orden = {}
        orden['permId'] = orderObj.permId
        orden['contractId'] = self.contractGetGconId(contractObj)
        orden['order'] = orderObj
        orden['params'] = paramsDict
        orden['Executed'] = False
        orden['toPrint'] = False
        orden['toCancel'] = False
        orden['strategy'] = None
        orden['ExecsList'] = {}
        str_o = self.orderSummary(orden)
        logging.info (str_o)
        
        try:
            self.orderList_.append(orden)
            result = True
        except:
            self.error(900, "Error añadiendo orden")
            
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
            pass
            #return (False)
        
        if not contractObj == "":
            #print ('Actualizo cont')
            ret = self.contractAdd (contractObj)         # Normalmante al añadir la orden, añadimos y actualizamos el contrato    
        
        for orden in self.orderList_:
            if orden['order'].orderId == tempId:
            #if orden['permId'] == localPermId:
                if orden['permId'] == None or orden['permId'] == '' or str(orden['permId']) == '0':
                    orden['permId'] = localPermId
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
                        orden['params'] = []
                    orden['params'].update(paramsDict)
                orden['toPrint'] = True
                str_o = self.orderSummary(orden)
                if bChanged:
                    logging.info (str_o)
                else:
                    logging.debug (str_o)

                break
                
        if not exists:
            result = self.orderAdd (contractObj, orderObj, paramsDict)

        return (result)

    def orderReturnListAll(self):
        return self.orderList_


    def orderSetExecutedStatus (self, orderId, bExec):
        for orden in self.orderList_: 
            if orden['order'].orderId == orderId:
                orden['Executed'] = bExec
                return True
        return None

    def orderSetStrategy (self, orderId, strategyObj):
        for orden in self.orderList_: 
            if orden['order'].orderId == orderId:
                orden['strategy'] = strategyObj
                return True
        return None
    
    # Se ha ejecutado una orden y hay que ver si corresponde a alguna estrategia para temas de influx
    # Cada vez que se llega una ejecución la guardamos, y despues cuando llegan las comisiones, lo analizamos y mandamos a influx
    # Las comisiones no traen el orderId, por lo que hay que guardar las exec para enlazar la comission con la ordenId

    def orderAddExecData (self, data):

        if not 'executionObj' in data:
            return
        executionObj = data['executionObj']
        exec_contract = data['contractObj']
        orderId = executionObj.orderId
        logging.info ('[Execution (%d)] Orden Ejecutada. ExecId: %s', orderId,executionObj.execId)
        logging.info ('    Number/Price: %s at %s, Cumulative: %s,  AvgPrice: %s', executionObj.shares, executionObj.price,  executionObj.cumQty, executionObj.avgPrice)
        logging.info ('    Side: %s, Type: %s', executionObj.side, exec_contract.secType)



        # Localizo si pertenece una estrategia
        orden = self.orderGetByOrderId(orderId)
        currentSymbolStrategy = orden['strategy']
        #strategy = self.strategies_.strategyGetStrategyObjByOrderId (orderId)
        
        #if not strategy or 'classObject' not in strategy:
        if not currentSymbolStrategy:
            logging.info ('    Orden %d Ejecutada. Pero no pertenece a ninguna estrategia', orderId)
            return False   
        else:
            logging.info ('    Estrategia: %s [%s]', currentSymbolStrategy.straType_, currentSymbolStrategy.symbol_)
  

        #currentSymbolStrategy = strategy['classObject']

        # Miramos que la estrategia esté activada (debería)
        if currentSymbolStrategy and currentSymbolStrategy.stratEnabled_ == False:
            logging.error ('    Pero la estrategia esta disabled!!!!')
            #return False
        
        #orden = self.orderGetByOrderId(orderId)
        
        # Esto es por asegurar, por si solo llega el exec. No debería pasar
        if orden['Executed'] == False and currentSymbolStrategy:
            data2 = {'orderId': orderId, 'contractObj': exec_contract, 'orderObj': orden['order'], 'paramsDict':None }
            currentSymbolStrategy.strategyOrderUpdated (data2)  
        
        # Info de debug
        logging.debug ('Order Executed:')
        logging.debug ('  Symbol: %s (%s)', exec_contract.symbol, exec_contract.secType)
        logging.debug ('  ExecId: %s', executionObj.execId)
        logging.debug ('  OrderId/PermId: %s/%s', executionObj.orderId, executionObj.permId)
        logging.debug ('  Number/Price: %s at %s', executionObj.shares, executionObj.price)
        logging.debug ('  Cumulative: %s', executionObj.cumQty)
        logging.debug ('  Liquidity: %s',executionObj.lastLiquidity)
        
        # Pillamos el contrato para que Pandas y generamos el dict con los datos que ncesita Pandas
        gConId = orden['contractId']
        contract = self.contractGetContractbyGconId(gConId)
        
        # Guardo los datos para que luego sea facil tratarlos. 
        # Cada index tiene una ejecución, y cada orden puede tener varias ejecuciones
        # luego, cada index tiene cada leg independiente.

        data_new = {}
        data_new['ExecId'] = executionObj.execId
        data_new['OrderId'] = executionObj.orderId
        data_new['PermId'] = executionObj.permId
        data_new['Quantity'] = executionObj.shares
        data_new['Cumulative'] = executionObj.cumQty
        data_new['Side'] = executionObj.side
        data_new['execSecType'] = exec_contract.secType     # Solo guardamos las de la BAG (o el que sea el que lancé)
        data_new['numLegs'] = len(contract['contractReqIdLegs'])
        data_new['contractSecType'] = contract['contract'].secType
        #data_new['strategy_type'] = strategy['type']
        if currentSymbolStrategy:
            data_new['strategy_type'] = currentSymbolStrategy.straType_
        else:
            data_new['strategy_type'] = 'N/A'
        #data_new['lastFillPrice'] = orden['params']['lastFillPrice']
        data_new['lastFillPrice'] = executionObj.price
        
        # Nos quedamos con la parte mas significativa del index
        index1 = executionObj.execId[:executionObj.execId.index('.')]
        rest = executionObj.execId[executionObj.execId.index('.') + 1:]
        index2 = rest[:rest.index('.')]
        index = index1 + '.' + index2

        # Si el index recibido no está en la lista, lo añado
        if not index in orden['ExecsList']:
            orden['ExecsList'][index] = {}
            orden['ExecsList'][index]['realizedPnL'] = float(0)
            orden['ExecsList'][index]['Commission'] = float(0)
            orden['ExecsList'][index]['numLegs'] = data_new['numLegs']
            orden['ExecsList'][index]['legsDone'] = 0
            orden['ExecsList'][index]['Side'] = None
            orden['ExecsList'][index]['Quantity'] = 0
            orden['ExecsList'][index]['Cumulative'] = 0
            orden['ExecsList'][index]['lastFillPrice'] = float(0)
            orden['ExecsList'][index]['data'] = [] # Aquí guardamos cada una de las legs que me llegan, para luego recibir la commision
        
        # El qty/side lo pillo del index de la spread (me va a llegar uno de la spread y luego por cada leg)
        if data_new['contractSecType'] == data_new['execSecType']:
            lRemaining = orden['order'].totalQuantity - executionObj.cumQty
            if lRemaining > 0:
                logging.info ('    Aun no hemos cerrado todas las posciones. Vamos %d de %d', executionObj.cumQty, orden['order'].totalQuantity)
            else:
                logging.info ('    Todas las posiciones (%d) cerradas', executionObj.cumQty)
            orden['ExecsList'][index]['Side'] = data_new['Side']
            orden['ExecsList'][index]['Quantity'] = data_new['Quantity']
            orden['ExecsList'][index]['Cumulative'] = data_new['Cumulative']
            orden['ExecsList'][index]['lastFillPrice'] = float(data_new['lastFillPrice'])
        else:
            # Estos son los de cada leg. Aqui llenamos la lista, y la vaciamos en Commissiones
            orden['ExecsList'][index]['data'].append(data_new)

        #if data_new['lastFillPrice'] != 0:
        #    orden['ExecsList'][index]['lastFillPrice'] = float(data_new['lastFillPrice'])
    
    def orderAddCommissionData (self, data):

        if not 'CommissionReport' in data:
            return

        dataCommission = data ['CommissionReport']

        index1 = dataCommission.execId[:dataCommission.execId.index('.')]
        rest = dataCommission.execId[dataCommission.execId.index('.')+1:]
        index2 = rest[:rest.index('.')]
        index = index1 + '.' + index2

        orden = self.orderGetOrderbyExecId(index)
        if not orden:
            logging.error('[Comision (%s)] Esta comissionReport no es de ninguna orden mia', dataCommission.execId)
            return False

        currentSymbolStrategy = orden['strategy']

        orderId = orden['order'].orderId
        #strategy = self.strategies_.strategyGetStrategyObjByOrderId (orderId)
        
        #if not strategy or 'classObject' not in strategy:
        if not currentSymbolStrategy:
            logging.info('[Comision (%s)] Esta comissionReport no es de ninguna orden que tenga estrategia. ExecId: %s', orderId, dataCommission.execId)
            return False
        else:
            logging.info ('[Comision (%s)] Commission en Estrategia %s [%s]. ExecId: %s', orderId, currentSymbolStrategy.straType_, currentSymbolStrategy.symbol_, dataCommission.execId)
        logging.info ('    Comission: %s. RealizedPnL: %s', dataCommission.commission, dataCommission.realizedPNL)

        gConId = orden['contractId']
        contract = self.contractGetContractbyGconId(gConId)
        lSymbol = contract['fullSymbol']

        # Cada orden puede tener varios ExecId. Uno por cada partial fill
        dataExec = None
        for exec in orden['ExecsList'][index]['data']: 
            if  dataCommission.execId == exec['ExecId']:
                dataExec = exec
                break
        if not dataExec:
            logging.error ('[Comision (%s)] Comision sin tener la info de la Orden ExecId (%s) anteriormente. Estrategia %s [%s]', orderId, dataCommission.execId, currentSymbolStrategy.straType_, currentSymbolStrategy.symbol_)
            return False

        if dataCommission.realizedPNL != UNSET_DOUBLE:  # Este valor lo usa IB para indicar empty cell.
            orden['ExecsList'][index]['realizedPnL'] += dataCommission.realizedPNL
        if dataCommission.commission != UNSET_DOUBLE:
            orden['ExecsList'][index]['Commission'] += dataCommission.commission
        orden['ExecsList'][index]['legsDone'] += 1

        logging.info ('    Comision acumulada: [%s]', orden['ExecsList'][index]['Commission'])
        logging.info ('    RealizedPnL acumulada: [%s]', orden['ExecsList'][index]['realizedPnL'])
        logging.info ('    Order price: [%s]', orden['ExecsList'][index]['lastFillPrice'])

        orden['ExecsList'][index]['data'].remove(dataExec) # por si llegan dos comisiones al mismo Exec (no deberia)

        # Miro a ver si tengo todos los legs de todos los index
        if orden['ExecsList'][index]['legsDone'] < orden['ExecsList'][index]['numLegs']:
            logging.info ('    El numero de legs de comision recibidas [%s] es inferior al del contrato [%s]. Esperamos el resto.', orden['ExecsList'][index]['legsDone'], orden['ExecsList'][index]['numLegs'])
            return True

        # Si llegamos aquí, es que tenemos las Commissions de este fill
        # Pude haber varios por cada orden
        # Los mando todos a pandas/influx
        

        time = datetime.datetime.now()
        time = utils.date2local (time)
        dataFlux = {}
        dataFlux['timestamp'] = time
        dataFlux['ExecId'] = index + '01.01'
        dataFlux['Symbol'] = lSymbol
        dataFlux['OrderId'] = dataExec['OrderId']
        dataFlux['PermId'] = dataExec['PermId']
        dataFlux['Quantity'] = orden['ExecsList'][index]['Quantity'] 
        dataFlux['Side'] = orden['ExecsList'][index]['Side'] 
        dataFlux['RealizedPnL'] = orden['ExecsList'][index]['realizedPnL'] 
        dataFlux['Commission'] = orden['ExecsList'][index]['Commission'] 
        dataFlux['FillPrice'] = orden['ExecsList'][index]['lastFillPrice'] 
        # Aqui seguimos con le escritura a Flux
        # Y borrar todo el orden['ExecsList'][index]
        logging.info ('    Commission Order Finalizada [100%]')

        if currentSymbolStrategy:
            currentSymbolStrategy.pandas_.dbAddCommissionsOrderFill(dataFlux)
        else:
            # Este es elgenerico para las execs que no tiene strat
            self.strategies_.pandasNoStrat_.dbAddCommissionsOrderFill(dataFlux)
      
        orden['ExecsList'].pop(index)

        return True

    def orderGetOrderbyExecId(self, index):
        for orden in self.orderList_:
            if index in orden['ExecsList']:
                return orden
    
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
        logging.debug ('[Orden %s] No encontrada', str(orderId))
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

    def orderPlaceBrief (self, symbol, contractObj, secType, action, oType, lmtPrice, qty):
        newreqDownId = self.appObj_.placeOrderBrief (symbol, contractObj, secType, action, oType, lmtPrice, qty) 
        return newreqDownId

    def orderPlaceBracket (self, symbol, contractObj, secType, action, qty, lmtPrice, takeProfitLimitPrice, stopLossPrice):
        ordersIds = self.appObj_.placeBracketOrder (symbol, contractObj, secType, action, qty, lmtPrice, takeProfitLimitPrice, stopLossPrice) 
        return ordersIds

    def orderPlaceOCA (self, symbol, contractObj, secType, actionSL, actionTP, qty, LmtPriceTP, LmtPriceSL):
        ordersIds = self.appObj_.placeOCAOrder (symbol, contractObj, secType, actionSL, actionTP, qty, LmtPriceTP, LmtPriceSL) 
        return ordersIds

    def orderUpdateOrder (self, symbol, contractObj, orderObj):
        orderId = self.appObj_.updateOrder (symbol, contractObj, orderObj) 
        return orderId

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
        summaryStr += ', ' + orden['order'].orderType
        if orden['order'].orderType[:3] == 'LMT':
            summaryStr += ': $' + str(orden['order'].lmtPrice)
        if orden['order'].orderType[:3] == 'STP':
            summaryStr += ': $' + str(orden['order'].auxPrice)
        summaryStr += ', Qty: ' + str(orden['order'].totalQuantity)
        summaryStr += '(' + filled + '/' + remaining + ') Filled Price: $' +  lastFillPrice
        

            
        
        # summaryStr += ', ' + self.contractSummaryPricesOnly(orden['contractId'])

        #orden['toPrint'] = False
                
        return summaryStr
                
 
