import websockets
import asyncio

class wsServer:
    def __init__(self, appObj, RtDataObj):
        self.clients = set()
        self.appObj_ = appObj
        self.LocalRT_ = RtDataObj
        self.appObj_.wsServerInt_ = self
        self.LocalRT_.wsServerInt_ = self
        
        self.ws = []
        
    async def websocket_request_handler(self, websocket, path):
        self.ws.append(websocket)
        comando = None
        while True:
        # receive the client websocket send data.
            try:
                client_data = await websocket.recv()
            except websockets.ConnectionClosedOK:
                break
            except websockets.ConnectionClosedError:
                break
            except:
                break 
            # construct the response data.
            if client_data:
                try: 
                    client_data = client_data.upper()
                    comando = client_data.split(' ')[0]
                    print (client_data)
                except:
                    print ('Error con comando')
                    return
            if self.appObj_.initConnected_ == False:
                response = 'La API no está lista todavía. Espera...'
                await self.ws[len(self.ws)-1].send(response)
                return
            if comando == 'LIST':
                await self.list_cmds (client_data)
            if comando == 'ORDEN':
                await self.orden_cmds (client_data)
         
            #await websocket.send(response_data)
    async def orden_cmds (self, cmd):
        try:
            if (len (cmd.split(' ')) < 2):
                return
        except:
            return
        secType = cmd.split(' ')[1]
        errorcmd = False

        if secType == 'FUT' or secType == 'STK' :
            print (cmd)
            response = ''
            # orden secType action symb type min_val qty
            # orden FUT     SELL   APPL LMT  1.23    2
            if (len (cmd.split(' ')) < 7):
                response = "Faltan argumentos"
                errorcmd = True
            else:
                action = cmd.split(' ')[2]
                if action != 'BUY' and action != 'SELL':
                    response = "Argumento 'action' debe ser 'SELL' o 'BUY'" 
                    errorcmd = True
                symbol = cmd.split(' ')[3]
                oType = cmd.split(' ')[4]
                if oType != 'LMT' and oType != 'MKT':
                    response = "Argumento 'oType' debe ser 'MKT' o 'LMT'" 
                    errorcmd = True
                try:
                    lmtPrice = float(cmd.split(' ')[5])
                except:
                    response = "La lmtPrice esta mal" 
                    errorcmd = True
                try:
                    qty = int(cmd.split(' ')[6])
                except:
                    response = "La qty esta mal" 
                    errorcmd = True
            
            if not errorcmd:
                try:
                    self.appObj_.placeOrderBrief (symbol, secType, action, oType, lmtPrice, qty)
                    response = '202 Orden Lanzada'
                except:
                    response = 'Error placing order'

            await self.ws[len(self.ws)-1].send(response)

        elif secType == 'CANCEL':
            if (len (cmd.split(' ')) < 3):
                response = "Faltan argumentos"
            else:
                orderId = cmd.split(' ')[2]
                if orderId == 'ALL':
                    try:
                        self.appObj_.cancelOrderAll ()
                    except:
                        response = '503 Error al cancelar'
                    else:
                        response = '202 Cancelacion de todas las ordenes Lanzada'
                else:
                    try:
                        result = self.appObj_.cancelOrderByOrderId (orderId)
                    except:
                        response = '503 Error al cancelar'
                    else:
                        if result:
                            response = '202 Cancelacion ' + str(orderId) + 'Orden Lanzada'
                        else:
                            response = '404 Orden no encontrada'
            await self.ws[len(self.ws)-1].send(response)

        else:
            await self.ws[len(self.ws)-1].send('SecType no reconocido')

    async def list_cmds (self, cmd):
        if not cmd:
            return
        cmd_list = cmd.split()
        if len(cmd_list) < 2:
            return
        if cmd_list[1] == 'ORDENES':
            #response = '202 Command executed'
            response = self.LocalRT_.orderSummaryAllBrief()
            await self.ws[len(self.ws)-1].send(response)
            #self.appObj_.reqOpenOrders()
        elif cmd_list[1] == 'ORDEN':
            if len(cmd_list) < 3:
                return
            if not cmd_list[2].isnumeric():
                return
            response = self.LocalRT_.orderSummaryFullByOrderId(int(cmd_list[2]))
            await self.ws[len(self.ws)-1].send(response)
        elif cmd_list[1] == 'POSICIONES':
            response = self.LocalRT_.positionSummaryAllBrief()
            await self.ws[len(self.ws)-1].send(response)
        elif cmd_list[1] == 'CONTRATOS':
            response = self.LocalRT_.contractSummaryAllBriefWithPrice()
            await self.ws[len(self.ws)-1].send(response)
        elif cmd_list[1] == 'CONTRATO':
            if len(cmd_list) < 3:
                return
            if not cmd_list[2].isnumeric():
                return
            response = self.LocalRT_.contractSummaryFullWithPrice(int(cmd_list[2]))
            await self.ws[len(self.ws)-1].send(response)
        return 
        
    async def print_text (self, text):
        if len(self.ws)> 0:
            await self.ws[len(self.ws)-1].send(text)
        
        
    async def start_websocket_server (self, host, port_number):
        '''
        # create the websocket server with the provided handler, host, and port_number.
        websocket_server = websockets.serve(websocket_request_handler, host, port_number)
     
        print('websocket server is running and listening on port number : ' + str(port_number))
    
        # run the websocket server asynchronouslly.
        asyncio.get_event_loop().run_until_complete(websocket_server)
        asyncio.get_event_loop().run_forever()
        '''
        
        async with websockets.serve(self.websocket_request_handler, host, port_number):
            await asyncio.Future()  # run forever
        
    def print_string (self, text):
        asyncio.run(self.print_text(text))

    def wsServerIB (self):
        host = "localhost"
    
        port_number = 9998
    
        asyncio.run(self.start_websocket_server(host, port_number) )
        
