orderChildErrorStatus = ['Inactive']
orderChildValidExecStatusParentFilled = ['Filled', 'Submitted', 'Cancelled', 'PreSubmitted', 'PendingCancel', 'ApiCancelled']
orderChildInvalidExecStatusParentNotFilled = ['Filled', 'Submitted', 'Cancelled', 'PendingCancel', 'ApiCancelled']
orderInactiveStatus = ['Cancelled', 'PendingCancel', 'Inactive', 'ApiCancelled']

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
    
    logging.info ('############## %s', bracketOrder)

    if bError:
        return None
    else:
        return bracketOrder

def bracketOrderParseToFile(bracketOrder):
    line = bracketOrder['B_S'] + ','
    line += str(bracketOrder['Price']) + ','
    line += str(bracketOrder['Qty']) + ','
    line += str(bracketOrder['PrecioSL']) + ','
    line += str(bracketOrder['PrecioTP']) + ','
    line += str(bracketOrder['OrderId']) + ','
    line += str(bracketOrder['OrderPermId']) + ','
    line += str(bracketOrder['OrderIdSL']) + ','
    line += str(bracketOrder['OrderPermIdSL']) + ','
    line += str(bracketOrder['OrderIdTP']) + ','
    line += str(bracketOrder['OrderPermIdTP']) + ','
    line += str(bracketOrder['BracketOrderFilledState'])
    line += '\n'
    return line

class bracketOrderClass():

    def __init__(self, data = None, RTlocalData = None):
        self.symbol_ = None
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

        self.RTLocalData_ = RTlocalData

        if data and 'symbol' in data:
            self.symbol_ = data['symbol']
        if data and 'orderId' in data:
            self.orderId_ = data['orderId']
        if data and 'orderIdSL' in data:
            self.orderIdSL_ = data['orderIdSL']
        if data and 'orderIdTP' in data:
            self.orderIdTP_ = data['orderIdTP']
        if data and 'orderPermId' in data:
            self.orderPermId_ = data['orderPermId']
        if data and 'orderPermIdSL' in data:
            self.orderPermIdSL_ = data['orderPermIdSL']
        if data and 'orderPermIdTP' in data:
            self.orderPermIdTP_ = data['orderPermIdTP']
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

    def strategyGetIfOrderPermId(self, orderPermId):
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
                err_msg += "\n[Estrategia PentagramaRu (%s)]. Error en parentId" % self.symbol_
                err_msg += "    \nEl parentId es None"
                bRehacerConError = True
            elif not bParentOrderExists:
                err_msg += "\n[Estrategia PentagramaRu (%s)]. Error en parentId" % self.symbol_
                err_msg += "    \nEl parentId [%s] no existe segun IB" % self.orderId_
                bRehacerConError = True
            elif bParentOrderStatus in orderInactiveStatus:
                err_msg += "\n[Estrategia PentagramaRu (%s)]. Error en parentId" % self.symbol_
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
                continue
        # Si hemos detectado error en parent, borramos todas si no existen
        elif bRehacerConError: # La parentId no está, y no está ejecutada. Borramos todas y rehacemos
            if (datetime.datetime.now() - self.timelasterror_) < Error_orders_timer_dt:
                continue
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
                continue
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
                logging.info ('[Estrategia PentagramaRu (%s)]. Todo ejecutado rehacemos', self.symbol_)
                ret = self.orderBlockCreateBracketOrder ()
            elif bRehacerTodo:
                logging.error ('[Estrategia PentagramaRu (%s)]. Rehacemos todo', self.symbol_)
                ret = self.orderBlockCreateBracketOrder ()
            elif bGenerarOCA:
                logging.error ('[Estrategia PentagramaRu (%s)]. Rehacemos OCA para childs', self.symbol_)
                ret = self.orderBlockCreateChildOca ()
            if ret != None:
                bBracketUpdated = True

        return bBracketUpdated

    def orderBlockOrderUpdated (self, data):
        #data['orderId']
        #data['orderStatus']

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
            '''
            if self.stratEnabled_:
                logging.info ('###################################################')
                logging.info ('ALARMA !!!!!!!')
                logging.info ('Estrategia: PentagramaRu [%s]', self.symbol_)
                logging.info ('Nos hemos salido por SL. Caquita')
                logging.info ('Paramos la estrategia porque estamos fuera de rango')
                self.stratEnabled_ = False
            '''
            bChanged = True
        
        return bChanged

    def orderBlockOrderIdUpdated (self, ordenObj):
        bChanged = False
        symbol = self.symbol_

        if self.orderPermId_ == None and self.orderId_ == ordenObj.orderId:
            logging.info ('[Estrategia PentagramaRu (%s)] Orden actualizada. Nueva OrderPermId: %s', symbol, ordenObj.permId)
            self.orderPermId_ = ordenObj.permId
            bChanged = True
        elif self.orderPermIdSL_ == None and self.orderIdSL_ == ordenObj.orderId:
            logging.info ('[Estrategia PentagramaRu (%s)] Orden actualizada. Nueva OrderPermIdSL: %s', symbol, ordenObj.permId)
            self.orderPermIdSL_ = ordenObj.permId
            bChanged = True
        elif self.orderPermIdTP_ == None and self.orderIdTP_ == ordenObj.orderId:
            logging.info ('[Estrategia PentagramaRu (%s)] Orden actualizada. Nueva OrderPermIdTP: %s', symbol, ordenObj.permId)
            self.orderPermIdTP_ = ordenObj.permId
            bChanged = True
        elif self.orderPermId_ == ordenObj.permId and self.orderId_ != ordenObj.orderId:  # Esto es por si el orderId cambia (el permId no puede cambiar)
            logging.info ('[Estrategia PentagramaRu (%s)] Orden actualizada (o inicializamos). Nueva OrderId: %s', symbol, ordenObj.orderId)
            self.orderId_ = ordenObj.orderId
            bChanged = True
        elif self.orderPermIdSL_ == ordenObj.permId and self.orderIdSL_ != ordenObj.orderId:  # Esto es por si el orderId cambia (el permId no puede cambiar)
            logging.info ('[Estrategia PentagramaRu (%s)] Orden actualizada (o inicializamos). Nueva OrderIdSL: %s', symbol, ordenObj.orderId)
            self.orderIdSL_ = ordenObj.orderId
            bChanged = True
        elif self.orderPermIdTP_ == ordenObj.permId and self.orderIdTP_ != ordenObj.orderId:  # Esto es por si el orderId cambia (el permId no puede cambiar)
            logging.info ('[Estrategia PentagramaRu (%s)] Orden actualizada (o inicializamos). Nueva OrderIdTP: %s', symbol, ordenObj.orderId)
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

    def orderBlockCreateBracketOrder (self, zone):

        symbol = self.symbol_
        contract = self.RTLocalData_.contractGetBySymbol(symbol)  
        secType = contract['contract'].secType
        action = 'BUY' if self.B_S_ == 'B' else 'SELL'
        qty = self.Qty_
        lmtPrice = self.Price_
        takeProfitLimitPrice = self.PrecioTP_
        stopLossPrice = self.PrecioSL_

        try:
            logging.info ('[Estrategia PentagramaRu (%s)]. Vamos a crear la triada de ordenes bracket', symbol)
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
        logging.info ('[Estrategia PentagramaRu (%s)]. Estas son las ordenes nuevas', symbol)
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
            logging.info ('[Estrategia PentagramaRu (%s)]. Vamos a crear las ordenes SL/TP como OCA', symbol)
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