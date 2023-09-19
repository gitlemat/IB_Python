import logging
import datetime

logger = logging.getLogger(__name__)

orderChildErrorStatus = ['Inactive']
orderChildValidExecStatusParentFilled = ['Filled', 'Submitted', 'Cancelled', 'PreSubmitted', 'PendingCancel', 'ApiCancelled']
orderChildInvalidExecStatusParentNotFilled = ['Filled', 'Submitted', 'Cancelled', 'PendingCancel', 'ApiCancelled']
orderInactiveStatus = ['Cancelled', 'PendingCancel', 'Inactive', 'ApiCancelled']
Error_orders_timer_dt = datetime.timedelta(seconds=90)

def bracketOrderParseFromFile(fields):
    bError = False
    bracketOrder = {}
    try:
        bracketOrder['B_S'] = fields[0].strip()
        bracketOrder['Price'] = float(fields[1].strip())
        bracketOrder['Qty'] = int(fields[2].strip())
        bracketOrder['PrecioSL'] = float(fields[3].strip())
        bracketOrder['PrecioTP'] = float(fields[4].strip())
    except:
        bError = True
    if fields[5].strip() == ''  or fields[5].strip() == 'None':
        bracketOrder['OrderId'] = None
    else:
        bracketOrder['OrderId'] = int (fields[5].strip())
    if fields[6].strip() == ''  or fields[6].strip() == 'None':
        bracketOrder['OrderPermId'] = None
    else:
        bracketOrder['OrderPermId'] = int (fields[6].strip())
    if fields[7].strip() == ''  or fields[7].strip() == 'None':
        bracketOrder['OrderIdSL'] = None
    else:
        bracketOrder['OrderIdSL'] = int (fields[7].strip())
    if fields[8].strip() == ''  or fields[8].strip() == 'None':
        bracketOrder['OrderPermIdSL'] = None
    else:
        bracketOrder['OrderPermIdSL'] = int (fields[8].strip())
    if fields[9].strip() == ''  or fields[9].strip() == 'None':
        bracketOrder['OrderIdTP'] = None
    else:
        bracketOrder['OrderIdTP'] = int (fields[9].strip())
    if fields[10].strip() == ''  or fields[10].strip() == 'None':
        bracketOrder['OrderPermIdTP'] = None
    else:
        bracketOrder['OrderPermIdTP'] = int (fields[10].strip())
    if fields[11].strip() == 'ParentFilled' or fields[11].strip() == 'ParentFilled+F' or fields[11].strip() == 'ParentFilled+C' :
        bracketOrder['BracketOrderFilledState'] = fields[11].strip()
    else:
        bracketOrder['BracketOrderFilledState'] = None
    
    logging.debug ('############## %s', bracketOrder)

    if bError:
        return None
    else:
        return bracketOrder

def bracketOrderParseToFile(bracketOrder):
    line = bracketOrder.B_S_ + ','
    line += str(bracketOrder.Price_) + ','
    line += str(bracketOrder.Qty_) + ','
    line += str(bracketOrder.PrecioSL_) + ','
    line += str(bracketOrder.PrecioTP_) + ','
    line += str(bracketOrder.orderId_) + ','
    line += str(bracketOrder.orderPermId_) + ','
    line += str(bracketOrder.orderIdSL_) + ','
    line += str(bracketOrder.orderPermIdSL_) + ','
    line += str(bracketOrder.orderIdTP_) + ','
    line += str(bracketOrder.orderPermIdTP_) + ','
    line += str(bracketOrder.BracketOrderFilledState_)
    line += '\n'
    return line

class bracketOrderClass():

    def __init__(self, data , symbol, straType, regenerate, RTlocalData):
        self.symbol_ = symbol
        self.orderId_ = None
        self.orderIdSL_ = None
        self.orderIdTP_ = None
        self.orderPermId_ = None
        self.orderPermIdSL_ = None
        self.orderPermIdTP_ = None
        self.BracketOrderFilledState_ = None
        self.B_S_ = None
        self.Qty_ = None
        self.Price_ = None
        self.PrecioTP_ = None
        self.PrecioSL_ = None
        self.strategyType_ = straType

        self.RTLocalData_ = RTlocalData
        self.regenerate_ = regenerate
        self.timelasterror_ = datetime.datetime.now()

        if data and 'OrderId' in data:
            self.orderId_ = data['OrderId']
        if data and 'OrderIdSL' in data:
            self.orderIdSL_ = data['OrderIdSL']
        if data and 'OrderIdTP' in data:
            self.orderIdTP_ = data['OrderIdTP']
        if data and 'OrderPermId' in data:
            self.orderPermId_ = data['OrderPermId']
        if data and 'OrderPermIdSL' in data:
            self.orderPermIdSL_ = data['OrderPermIdSL']
        if data and 'OrderPermIdTP' in data:
            self.orderPermIdTP_ = data['OrderPermIdTP']
        if data and 'BracketOrderFilledState' in data:
            self.BracketOrderFilledState_ = data['BracketOrderFilledState']

        if data and 'B_S' in data:
            self.B_S_ = data['B_S']
        if data and 'Qty' in data:
            self.Qty_ = data['Qty']
        if data and 'Price' in data:
            self.Price_ = data['Price']
        if data and 'PrecioTP' in data:
            self.PrecioTP_ = data['PrecioTP']
        if data and 'PrecioSL' in data:
            self.PrecioSL_ = data['PrecioSL']

        logging.info ('Order Block:')
        logging.info ('------------')
        logging.info ('Symbol: %s', self.symbol_)
        logging.info ('orderId: %s', self.orderId_)
        logging.info ('orderIdSL: %s', self.orderIdSL_)
        logging.info ('orderIdTP: %s', self.orderIdTP_)

        # To override
        return None

    def orderBlockSubscribeOrdersInit (self): 
        
        if self.orderId_ != None:
            self.RTLocalData_.orderSetStrategy (self.orderId_, self)
        if self.orderIdSL_ != None:
            self.RTLocalData_.orderSetStrategy (self.orderIdSL_, self)
        if self.orderIdTP_ != None:
            self.RTLocalData_.orderSetStrategy (self.orderIdTP_, self)


    def orderBlockGetIfOrderId(self, orderId):
        if self.orderId_ == orderId or self.orderIdSL_ == orderId or self.orderIdTP_ == orderId:
            return True
        return False

    def orderBlockGetIfOrderPermId(self, orderPermId):
        if self.orderPermId_ == orderPermId or self.orderPermIdSL_ == orderPermId or self.orderPermIdTP_ == orderPermId:
            return True
        return False


    def orderBlockLoopCheck(self):
        # Potenciales estados de error:
        # Parent no ejecutada:
        #     - Sintomas:
        #         - Parent_id Null
        #         - Parent_id no existe segun IB
        #         - Parent order en estado inactivo ['Cancelled', 'PendingCancel', 'Inactive', 'ApiCancelled']
        #     - Accion:
        #         - Rehacer todo
        #     - Sintomas:
        #         - SL_id o TP_id Null
        #         - SL_id o TP_id no existe segun IB
        #         - SL_id o TP_id en estado erroneo orderChildInvalidExecStatusParentNotFilled -> ['Filled', 'Submitted', 'Cancelled', 'PendingCancel', 'ApiCancelled']
        #     - Accion:
        #         - Rehacer las TP/SL (seguramente deshaciendo la que esta bien). Entiendo que se puede hacer usando parent_id
        #         - Quizá es mejor deshacer/cancel todo y rehacer
        # Parent ejecutada:
        #     - Sintoma:
        #         - SL_id o TP_id Null
        #         - SL_id o TP_id no existe segun IB
        #         - SL_id o TP_id en estado erroneo NO EN orderChildValidExecStatusParentFilled -> ['Filled', 'Submitted', 'Cancelled', 'PendingCancel', 'ApiCancelled']
        #     - Accion:
        #         - Rehacer las TP/SL pero quizá haciendo un OCA nuevo. Follon necesario
        # En todos los casos:
        #     - Sintoma:
        #         - SL_id o TP_id Null
        #         - SL_id o TP_id no existe segun IB
        #     - Accion:
        #         - Rehacer las TP/SL dependiendo de si la parent está ejecutada o no
        #         - Si la parent está exec: OCA
        #         - Si la parent no está exec: igual hay que rehacer todo.


        bBracketUpdated = False

        bRehacerNoError = False
        err_msg = ""
        bRehacerConError = False
        bParentOrderExists = self.RTLocalData_.orderCheckIfExistsByOrderId(self.orderId_)
        bParentOrderStatus = self.RTLocalData_.orderGetStatusbyOrderId (self.orderId_)
        bSLOrderError = False
        bSLOrderExists = self.RTLocalData_.orderCheckIfExistsByOrderId(self.orderIdSL_)
        bSLOrderStatus = self.RTLocalData_.orderGetStatusbyOrderId (self.orderIdSL_)
        bTPOrderError = False
        bTPOrderExists = self.RTLocalData_.orderCheckIfExistsByOrderId(self.orderIdTP_)
        bTPOrderStatus = self.RTLocalData_.orderGetStatusbyOrderId (self.orderIdTP_)
        # Si no tengo constancia de que se halla comprado la parent, si no existe es error
        if self.BracketOrderFilledState_ == None:
            if self.orderId_ == None:
                err_msg += "\n[Estrategia %s (%s)]. Error en parentId" % (self.strategyType_, self.symbol_)
                err_msg += "    \nEl parentId es None"
                bRehacerConError = True
            elif not bParentOrderExists:
                err_msg += "\n[Estrategia %s (%s)]. Error en parentId" % (self.strategyType_, self.symbol_)
                err_msg += "    \nEl parentId [%s] no existe segun IB" % self.orderId_
                bRehacerConError = True
            elif bParentOrderStatus in orderInactiveStatus:
                err_msg += "\n[Estrategia %s (%s)]. Error en parentId" % (self.strategyType_, self.symbol_)
                err_msg += "    \nEl parentId [%s] tiene un estado invalido: %s" % (self.orderId_, bParentOrderStatus)
                bRehacerConError = True
            # Parent no ejecutada y está perfectamente, y error en child
            elif bSLOrderStatus in orderChildInvalidExecStatusParentNotFilled:
                err_msg += "    \nEl SLOrder [%s] tiene un estado invalido: %s" % (self.orderIdSL_,bSLOrderStatus)
                bSLOrderError = True
            elif bTPOrderStatus in orderChildInvalidExecStatusParentNotFilled:
                err_msg += "    \nEl TPOrder [%s] tiene un estado invalido: %s" % (self.orderIdTP_,bTPOrderStatus)
                bTPOrderError = True
        elif self.BracketOrderFilledState_ in ['ParentFilled+F']:
            bRehacerNoError = True
        # Si la parentOrder se ha ejecutado, las child tienen que estar en un estado valido. Si no error.                
        else:
            if bSLOrderStatus == 'Filled' and bTPOrderStatus == 'Cancelled': # Todo ejecutado
                bRehacerNoError = True
            if bSLOrderStatus == 'Cancelled' and bTPOrderStatus == 'Filled':
                bRehacerNoError = True
            if not bSLOrderExists:
                err_msg += "    \nLa parent [%s] está executada." % self.orderId_
                err_msg += "    \nEl SLOrder [%s] no existe segun IB. Asumimos que todo se ha hecho" % self.orderIdSL_
                bRehacerConError = True 
            if not bTPOrderExists:
                err_msg += "    \nLa parent [%s] está executada." % self.orderId_
                err_msg += "    \nEl TPOrder [%s] no existe segun IB. Asumimos que todo se ha hecho" % self.orderIdTP_
                bRehacerConError = True 
            if bSLOrderStatus in orderInactiveStatus and bTPOrderStatus in orderInactiveStatus:
                err_msg += "    \nEl SLOrder [%s] tiene un estado inválido: %s, y la parent [%s] esta ejecutada" % (self.orderIdSL_,bSLOrderStatus, self.orderId_)
                err_msg += "    \nEl TPOrder [%s] tiene un estado inválido: %s, y la parent [%s] esta ejecutada" % (self.orderIdTP_,bTPOrderStatus, self.orderId_)
                bSLOrderError = True
                bTPOrderError = True
            if bSLOrderStatus not in orderChildValidExecStatusParentFilled:
                err_msg += "    \nEl SLOrder [%s] tiene un estado inválido: %s, y la parent [%s] esta ejecutada" % (self.orderIdSL_,bSLOrderStatus, self.orderId_)
                bSLOrderError = True
            if bTPOrderStatus not in orderChildValidExecStatusParentFilled:
                err_msg += "    \nEl TPOrder [%s] tiene un estado inválido: %s, y la parent [%s] esta ejecutada" % (self.orderIdTP_,bTPOrderStatus, self.orderId_)
                bTPOrderError = True
        # Si la OrderSL no existe: error siempre.
        # El probable que aquí no entremos nunca sin haber entrada en una anterior de más prioridad
        if self.orderIdSL_ == None:
            err_msg += "    \nEl SLOrderId es None"
            bSLOrderError = True
        elif not bSLOrderExists:
            err_msg += "    \nEl SLOrder [%s] no existe segun IB" % self.orderIdSL_
            bSLOrderError = True
        # Si la OrderTP no existe: error siempre
        if self.orderIdTP_ == None:
            err_msg += "    \nEl TPOrderId es None"
            bTPOrderError = True   
        elif not bTPOrderExists:
            err_msg += "    \nEl TPOrder [%s] no existe segun IB" % self.orderIdTP_
            bTPOrderError = True              

        # Ahora vemos qué se hace por cada error
        #

        bRehacerTodo = False
        bGenerarOCA = False

        parentOrderId = self.orderId_                

        # Hay que rehacer, pero no es error
        if bRehacerNoError:
            if (datetime.datetime.now() - self.timelasterror_) < Error_orders_timer_dt:
                return bBracketUpdated
        # Si hemos detectado error en parent, borramos todas si no existen
        elif bRehacerConError: # La parentId no está, y no está ejecutada. Borramos todas y rehacemos
            if (datetime.datetime.now() - self.timelasterror_) < Error_orders_timer_dt:
                return bBracketUpdated
            parentOrderId = None
            logging.error (err_msg)
            if bParentOrderExists:
                logging.error ('    Cancelamos la Parent OrderId %s', self.orderId_)
                self.RTLocalData_.orderCancelByOrderId (self.orderId_)  
            if bSLOrderExists:
                logging.error ('    Cancelamos la SLOrder OrderId %s', self.orderIdSL_)
                self.RTLocalData_.orderCancelByOrderId (self.orderIdSL_)  
            if bSLOrderExists:
                logging.error ('    Cancelamos la OrderIdTP OrderId %s', self.orderIdTP_)
                self.RTLocalData_.orderCancelByOrderId (self.orderIdTP_)
            bRehacerTodo = True

        # Si hemos detectado error en alguna child, las borramos para recrear
        # Si no esta exec: borramos todo y recrear
        # Si ya esta exec: Hacemos a mano la TP y SL
        elif bSLOrderError or bTPOrderError:
            if (datetime.datetime.now() - self.timelasterror_) < Error_orders_timer_dt:
                return bBracketUpdated
            logging.error ('[Estrategia PentagramaRu (%s)]. Error en childOrder', self.symbol_)
            logging.error (err_msg)
            if bSLOrderExists:
                logging.error ('    Cancelamos la SLOrder OrderId %s', self.orderIdSL_)
                self.RTLocalData_.orderCancelByOrderId (self.orderIdSL_)  
            if bSLOrderExists:
                logging.error ('    Cancelamos la OrderIdTP OrderId %s', self.orderIdTP_)
                self.RTLocalData_.orderCancelByOrderId (self.orderIdTP_)  
            if self.BracketOrderFilledState_ not in ['ParentFilled', 'ParentFilled+F', 'ParentFilled+C']:
                logging.error ('    Cancelamos la Parent OrderId %s', self.orderId_)
                self.RTLocalData_.orderCancelByOrderId (self.orderId_)
                bRehacerTodo = True
            else:
                bGenerarOCA = True

        if bRehacerTodo or bGenerarOCA or bRehacerNoError:
            self.timelasterror_ = datetime.datetime.now()
            ret = None
            if bRehacerNoError:
                if self.regenerate_:
                    logging.info ('[Estrategia %s (%s)]. Todo ejecutado rehacemos', self.strategyType_, self.symbol_)
                    ret = self.orderBlockCreateBracketOrder ()
                else:
                    logging.info ('[Estrategia %s (%s)]. Todo ejecutado pero no rehacemos y salios', self.strategyType_, self.symbol_)
            elif bRehacerTodo:
                logging.error ('[Estrategia %s (%s)]. Rehacemos todo', self.strategyType_, self.symbol_)
                ret = self.orderBlockCreateBracketOrder ()
            elif bGenerarOCA:
                logging.error ('[Estrategia %s (%s)]. Rehacemos OCA para childs', self.strategyType_, self.symbol_)
                ret = self.orderBlockCreateChildOca ()
            if ret == None:
                bBracketUpdated = False
            elif ret == -1:
                bBracketUpdated = -1
            elif ret != None:
                bBracketUpdated = True

        return bBracketUpdated

    def orderBlockOrderUpdated (self, data):
        #data['orderId']
        #data['orderStatus']

        bChanged = False

        orderId = data['orderId']
        orderStatus = data['orderStatus']

        if self.orderId_ == orderId and orderStatus == 'Filled':
            self.BracketOrderFilledState_ = 'ParentFilled'
            bChanged = True
        if self.orderIdTP_ == orderId and orderStatus == 'Filled':
            self.BracketOrderFilledState_ = 'ParentFilled+F'
            bChanged = True
        if self.orderIdSL_ == orderId and orderStatus == 'Filled':
            self.BracketOrderFilledState_ = 'ParentFilled+F'
            bChanged = -1 # Es el error de salir por SL
        
        return bChanged

    def orderBlockOrderIdUpdated (self, ordenObj):
        bChanged = False
        symbol = self.symbol_

        if self.orderPermId_ == None and self.orderId_ == ordenObj.orderId:
            logging.info ('[Estrategia %s (%s)] Orden actualizada. Nueva OrderPermId: %s', self.strategyType_, symbol, ordenObj.permId)
            self.orderPermId_ = ordenObj.permId
            bChanged = True
        elif self.orderPermIdSL_ == None and self.orderIdSL_ == ordenObj.orderId:
            logging.info ('[Estrategia %s (%s)] Orden actualizada. Nueva OrderPermIdSL: %s', self.strategyType_, symbol, ordenObj.permId)
            self.orderPermIdSL_ = ordenObj.permId
            bChanged = True
        elif self.orderPermIdTP_ == None and self.orderIdTP_ == ordenObj.orderId:
            logging.info ('[Estrategia %s (%s)] Orden actualizada. Nueva OrderPermIdTP: %s', self.strategyType_, symbol, ordenObj.permId)
            self.orderPermIdTP_ = ordenObj.permId
            bChanged = True
        elif self.orderPermId_ == ordenObj.permId and self.orderId_ != ordenObj.orderId:  # Esto es por si el orderId cambia (el permId no puede cambiar)
            logging.info ('[Estrategia %s (%s)] Orden actualizada (o inicializamos). Nueva OrderId: %s', self.strategyType_, symbol, ordenObj.orderId)
            self.orderId_ = ordenObj.orderId
            bChanged = True
        elif self.orderPermIdSL_ == ordenObj.permId and self.orderIdSL_ != ordenObj.orderId:  # Esto es por si el orderId cambia (el permId no puede cambiar)
            logging.info ('[Estrategia %s (%s)] Orden actualizada (o inicializamos). Nueva OrderIdSL: %s', self.strategyType_, symbol, ordenObj.orderId)
            self.orderIdSL_ = ordenObj.orderId
            bChanged = True
        elif self.orderPermIdTP_ == ordenObj.permId and self.orderIdTP_ != ordenObj.orderId:  # Esto es por si el orderId cambia (el permId no puede cambiar)
            logging.info ('[Estrategia %s (%s)] Orden actualizada (o inicializamos). Nueva OrderIdTP: %s', self.strategyType_, symbol, ordenObj.orderId)
            self.orderIdTP_ = ordenObj.orderId
            bChanged = True

        return bChanged

    def orderBlockPosiciones(self):

        pos = 0
        BS = 1
        if self.B_S_ == 'S':
            BS = -1

        orderParent = self.RTLocalData_.orderGetByOrderId(self.orderId_)
        qty = 0
        if not orderParent:
            if self.BracketOrderFilledState_ == 'ParentFilled':
                qty = self.Qty_
        elif 'filled' in orderParent['params']:
            qty = orderParent['params']['filled']
        pos += qty * BS

        orderTP = self.RTLocalData_.orderGetByOrderId(self.orderIdTP_)
        qty = 0
        if orderTP and 'filled' in orderTP['params']:
            qty = orderTP['params']['filled']
        pos += qty * BS * (-1) # Las SL y TP tienen direccion contraria al parent

        orderSL = self.RTLocalData_.orderGetByOrderId(self.orderIdSL_)
        qty = 0
        if orderSL and 'filled' in orderSL['params']:
            qty = orderSL['params']['filled']
        pos += qty * BS * (-1) # Las SL y TP tienen direccion contraria al parent

        return pos

    def orderBlockCreateBracketOrder (self):

        symbol = self.symbol_
        contract = self.RTLocalData_.contractGetBySymbol(symbol)  
        secType = contract['contract'].secType
        action = 'BUY' if self.B_S_ == 'B' else 'SELL'
        qty = self.Qty_
        lmtPrice = self.Price_
        takeProfitLimitPrice = self.PrecioTP_
        stopLossPrice = self.PrecioSL_

        try:
            logging.info ('[Estrategia %s (%s)]. Vamos a crear la triada de ordenes bracket', self.strategyType_, symbol)
            logging.info ('     Precio LMT: %.3f', lmtPrice)
            logging.info ('     Precio TP : %.3f', takeProfitLimitPrice)
            logging.info ('     Precio SL : %.3f', stopLossPrice)
            orderIds = self.RTLocalData_.orderPlaceBracket (symbol, secType, action, qty, lmtPrice, takeProfitLimitPrice, stopLossPrice)
        except:
            logging.error('Error lanzando las barcket orders', exc_info = True)
            return None

        if orderIds == None:
            return None

        self.orderId_ = None
        self.orderIdSL_ = None
        self.orderIdTP_ = None
        self.orderPermId_ = None
        self.orderPermIdSL_ = None
        self.orderPermIdTP_ = None
        self.BracketOrderFilledState_ = None

        self.orderId_ = orderIds['parentOrderId']
        self.orderIdTP_ = orderIds['tpOrderId']
        self.orderIdSL_ = orderIds['slOrderId']
        self.orderPermId_ = None
        self.orderPermIdSL_ = None
        self.orderPermIdTP_ = None
        self.BracketOrderFilledState_ = None
        logging.info ('[Estrategia %s (%s)]. Estas son las ordenes nuevas', self.strategyType_, symbol)
        logging.info ('     Orden Pt: %s', self.orderId_)
        logging.info ('     Orden TP: %s', self.orderIdTP_)
        logging.info ('     Orden SL: %s', self.orderIdSL_)

        return True

    def orderBlockCreateChildOca (self):

        symbol = self.symbol_
        contract = self.RTLocalData_.contractGetBySymbol(symbol)  
        secType = contract['contract'].secType
        action1 = 'BUY' if self.B_S_ == 'B' else 'SELL'
        action2 = action1 # Es un SL , tiene que ser igual al TP
        qty = self.Qty_
        takeProfitLimitPrice = self.PrecioTP_
        stopLossPrice = self.PrecioSL_

        try:
            logging.info ('[Estrategia %s (%s)]. Vamos a crear las ordenes SL/TP como OCA', self.strategyType_,  symbol)
            logging.info ('     Precio TP : %.3f', takeProfitLimitPrice)
            logging.info ('     Precio SL : %.3f', stopLossPrice)
            orderIds = self.RTLocalData_.orderPlaceOCA (symbol, secType, action1, action2, qty, takeProfitLimitPrice, stopLossPrice)
        except:
            logging.error('Error lanzando las OCA orders', exc_info=True)
            return None

        if orderIds == None:
            return None

        self.orderIdTP_ = orderIds['tpOrderId']
        self.orderIdSL_ = orderIds['slOrderId']

        return True