import cmd
import threading
import time
import websocket

CLI_APP = None

class IB_CLI(cmd.Cmd):
    """Simple command processor example."""
    prompt = '> '
    intro = 'IB API - Command Line\n---------------------\n'
    def __init__(self, ws_p):
        super(IB_CLI, self).__init__()
        self.ws_p_ = ws_p

    def emptyline(self):
        pass

    def default(self, line):
        print ('comando desconocido')

    ############################
    # Orden commands
    
    def do_orden (self, line):
        try:
            if (len (line.split(' ')) < 1):
                return
        except:
            return
        line = line.upper()
        subcmd1 = line.split(' ')[0]
        errorcmd = False
        if subcmd1 == 'EJEMPLO1':
            line = 'FUT BUY HEV2-HEZ2 MKT 1 1'
        elif subcmd1 == 'EJEMPLO2':
            line = 'STK BUY AAPL MKT 1 1'
        elif subcmd1 == 'FUT' or subcmd1 == 'STK':
            response = ''
            # create orden action symb type min_val qty
            # create orden SELL APPL LMT 1.23 2
            if (len (line.split(' ')) < 6):
                response = "Faltan argumentos"
                errorcmd = True
            else:
                action = line.split(' ')[1]
                if action != 'BUY' and action != 'SELL':
                    response = "Argumento 'action' debe ser 'SELL' o 'BUY'" 
                    errorcmd = True
                symbol = line.split(' ')[2]
                oType = line.split(' ')[3]
                if oType != 'LMT' and oType != 'MKT':
                    response = "Argumento 'oType' debe ser 'MKT' o 'LMT'" 
                    errorcmd = True
                try:
                    lmtPrice = float(line.split(' ')[4])
                except:
                    response = "La lmtPrice esta mal" 
                    errorcmd = True
                try:
                    qty = int(line.split(' ')[5])
                except:
                    response = "La qty esta mal" 
                    errorcmd = True
        elif subcmd1 == 'CANCEL':
            if (len (line.split(' ')) < 2):
                response = "Faltan argumentos"
                errorcmd = True
        else:
            response = 'Subcomando no reconocido'
            errorcmd = True

        if errorcmd:
            print (response)
            return
        else:
            line = 'orden ' + line
            self.ws_p_.send(line)

    def help_orden (self):
        print ('     > orden [secType] [action] [symbol] [oType] [lmtPrice] [qty]')
        print ('       Ejemplo:')
        print ('       orden FUT BUY HEV2-HEZ2 LMT 1.20 1')
        print ('       orden STK BUY AAPL MKT 0 1')
        print ('       orden CANCEL 23')

    def complete_orden (self, text, line, begidx, endidx):
        ORDEN_CMDs = ['FUT','STK','OPT', 'CANCEL']
        if not text:
            completions = ORDEN_CMDs[:]
        else:
            completions = [ f
                            for f in ORDEN_CMDs
                            if f.startswith(text)
                            ]
        return completions

    ############################
    # List commands

    def do_list(self, line):
        #print (line)
        try:
            if (len (line.split(' ')) < 1):
                return
        except:
            return
        
        line = line.upper()
        subcmd1 = line.split(' ')[0]
        errorcmd = True
        response = 'Subcomando desconocido'
        if subcmd1 == 'ORDENES':    
            errorcmd = False
        elif subcmd1 == 'ORDEN':
            errorcmd = False
            if (len (line.split(' ')) < 2):
                errorcmd = True
                response = 'Falta el numero de order'
            elif not line.split(' ')[1].isnumeric():
                errorcmd = True
                response = 'Numero de orden mal puesto'
        elif subcmd1 == 'POSICIONES': 
            errorcmd = False
        elif subcmd1 == 'CONTRATOS': 
            errorcmd = False
        elif subcmd1 == 'CONTRATO':
            errorcmd = False
            if (len (line.split(' ')) < 2):
                errorcmd = True
                response = 'Falta el ContractId'
            elif not line.split(' ')[1].isnumeric():
                errorcmd = True
                response = 'Numero de orden mal puesto'
        if errorcmd:
            print (response)
            return
        else:
            line = 'list ' + line
            print (line)
            self.ws_p_.send(line)

    def help_list (self):
        print ('     > list objeto [IDs]')
        print ('       Ejemplo:')
        print ('       LIST ORDENES')
        print ('       LIST ORDEN 32')
        print ('       LIST CONTRATOS')
        print ('       LIST CONTRATO 112233')
        print ('       LIST POSICIONES')
        print ('       LIST POSICION 112233')
    
    def complete_list (self, text, line, begidx, endidx):
        LIST_CMDs = ['orden', 'ordenes','posicion','posiciones','estrategias', 'contrato', 'contratos']
        if not text:
            completions = LIST_CMDs[:]
        else:
            completions = [ f
                            for f in LIST_CMDs
                            if f.startswith(text)
                            ]
        return completions

    def do_exit(self, s):
        return True
    def help_exit(self):
        print ("Exit the interpreter.")
        print ("You can also use the Ctrl-D shortcut.")
    do_EOF = do_exit
    help_EOF= help_exit

def on_message(ws, message):
    print (message)
    CLI_APP.emptyline()

def on_close(ws):
    print ("### closed ###")

def on_error(ws, error):
    print(error)

if __name__ == '__main__':


    ws = websocket.WebSocketApp("ws://localhost:9998", on_message = on_message, on_error=on_error, on_close = on_close)
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()

    CLI_APP = IB_CLI(ws)

    cli_t = threading.Thread(target=CLI_APP.cmdloop)
    cli_t.daemon = True
    cli_t.start()

    conn_timeout = 5

    while not ws.sock.connected and conn_timeout:
        time.sleep(1)
        conn_timeout -= 1


    try:
        while True:
            time.sleep(1)
            pass
    except KeyboardInterrupt:
        print()