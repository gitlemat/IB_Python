# Esto habria que ir quitando dependencias de IB
#from ibapi.wrapper import *
#from ibapi.client import *
#from ibapi.contract import *
#from ibapi.order import *
#	from ibapi.order_condition import Create, OrderCondition

import globales
import threading
import logging, os
import argparse
import time
import datetime
import RT_LocalData
import IB_API_Client
import wsServer
import asyncio
import strategies
import webFE


def SetupLogger():
    if not os.path.exists("log"):
        os.makedirs("log")

    time.strftime("pyibapi.%Y%m%d_%H%M%S.log")

    #recfmt = '(%(threadName)s) %(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s'
    recfmt = '%(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s'

    timefmt = '%y-%m-%d_%H:%M:%S'

    # logging.basicConfig( level=logging.DEBUG,
    #                    format=recfmt, datefmt=timefmt)
    logging.basicConfig(filename=time.strftime("log/ibapi_sic.%y%m%d.log"),
                        filemode="w",
                        level=logging.DEBUG,
                        format=recfmt, datefmt=timefmt)
    logger = logging.getLogger()              # El root looger afecta a todos los demas
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler() # Esto sirve para que los INFO o más altos salgan por consola
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

def wsServer_loop(wsServer1):

    #wsServer1 = wsServer.wsServer(appObj)
    wsServer1.wsServerIB()

def webFE_loop():

    #wsServer1 = wsServer.wsServer(appObj)
    webFE.appDashFE_.run_server(port=5000, debug=False, threaded=True)
    
def run_loop(app):
	app.run()

def main():
    print("Iniciando demonio...")
    SetupLogger()
    logging.debug("now is %s", datetime.datetime.now())

    #globales.G_RTlocalData_ = None
    app = None
    wsServer1 = None
    strategyIns = None 

    # Parsing Parameters
    
    cmdLineParser = argparse.ArgumentParser("api tests")
    cmdLineParser.add_argument("-b", "--brief", action="store_true", default=False, help="Only brief prints")

    args = cmdLineParser.parse_args()
    
    # Init de RT_LocalData
    
    #globales.G_RTlocalData_ = RT_LocalData.DataLocalRT()
    globales.G_RTlocalData_.verboseBrief = args.brief
    
    # Init de IB_API_Client
    
    client_id = 0
    app = IB_API_Client.IBI_App("127.0.0.1", 4002, client_id, globales.G_RTlocalData_)
    t_api_thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    t_api_thread.start()

    strategyIns = strategies.Strategies(globales.G_RTlocalData_, app)
    
    # Init web page
    #webFE1 = webFE.webFE(globals.G_RTlocalData_)
    #t_webFE = threading.Thread(name='webFE', target=webFE_loop, args=(webFE1,))
    t_webFE = threading.Thread(name='webFE', target=webFE_loop)
    t_webFE.start()

    # Init de wsServer
    wsServer1 = wsServer.wsServer(app, globales.G_RTlocalData_)
    t_wsServerIB = threading.Thread(name='wsServerIB', target=wsServer_loop, args=(wsServer1,))
    t_wsServerIB.start()


    
    # Esperamos que esté conectado
    
    while True:
        if isinstance(app.nextorderId, int):
            logging.info("Conectado con TWS")
            app.initConnected_ = True
            break
        else:
            logging.info("Waiting for connection...")
            time.sleep(1)    

    # A printout to show the program began
    time.sleep (3)
    logging.info("Conexion establecida con TWS.")

    #assigning the return from our clock method to a variable 
    requested_time = app.server_clock()

    #printing the return from the server
    time_p = datetime.datetime.fromtimestamp( requested_time )
    logging.info("Hora de IB: %s", time_p)
    logging.info("Hora local: %s", datetime.datetime.now())

    app.reqAutoOpenOrders(True)
    
    app.reqPositions()    
    app.reqAllOpenOrders()
    app.reqAccountSummary(9001, "All", app.accSumTags.AllTags)
    
    while True:
        if app.initOrders_ and app.initPositions_ and app.initAccount_:
            app.initReady_ = True
            logging.info("Listo para operar")
            break
        else:
            logging.info("Esperando lista inicial de ordenes y posiciones")
            time.sleep(1)   
                               
    globales.G_RTlocalData_.contractLoadFixedWatchlist()

    app.reqMarketDataType(3)

    #app.reqAccountSummary(2, "all", "TotalCashValue" )
    
    ###########################################
    # Loop Principal
    try:
        while True:
            time.sleep(0.1)
            if app.initConnected_== False:
                app.initReady_ = False
                continue
            if app.initOrders_ == False:  # Conectado pero sin ordenes
                app.initReady_ = False
                # Primero hay que borrar la lista actual por si se han cerrado o cancelado ordenes
                globales.G_RTlocalData_.orderDeleteAll()
                app.reqAllOpenOrders()
                continue # Que no continue si initOrders_ == False
            if app.initPositions_ == False:
                app.initReady_ = False
                # Primero hay que borrar la lista actual por si se han cerrado o cancelado ordenes
                globales.G_RTlocalData_.positionDeleteAll()
                app.reqPositions()
                continue # Que no continue si initPositions_ == False
    
            contratosIncompletos = globales.G_RTlocalData_.contractCheckStatus()  # Ver si los BAGs tienen sus legs completas
                                                                                  # Y ver si tenemos todos los simbolos y subscripcion a tick
            if contratosIncompletos == True:
                app.initReady_ = False
                globales.G_RTlocalData_.contractReqDetailsAllMissing()
                continue

            strategyIns.strategyIndexCheckAll() # Compruebo las strategias

            if app.initReady_ == False:         # Si aqui está False, es que hemos recuperado
                app.initReady_ = True             # Si llegamos aquí es que todo bien
                globales.G_RTlocalData_.contractLoadFixedWatchlist()

            while app.CallbacksQueue_.empty() == False:
                callbackIten = app.CallbacksQueue_.get()
                if callbackIten['type'] == 'execution':
                    globales.G_RTlocalData_.executionAnalisys (callbackIten['data'])
                if callbackIten['type'] == 'tick':
                    globales.G_RTlocalData_.tickUpdatePrice (callbackIten['data'])
                if callbackIten['type'] == 'order':
                    order = callbackIten['data']['orderObj']
                    globales.G_RTlocalData_.orderUpdate(callbackIten['data'])
                    # Añadir algo que actualizar ordenes en Strategy
                    if not order=="":
                        strategyIns.strategyIndexOrderUpdate (order) # Se hace desde RTData que tiene el objeto
                if callbackIten['type'] == 'position':
                    globales.G_RTlocalData_.positionUpdate (callbackIten['data'])
                if callbackIten['type'] == 'account':
                    globales.G_RTlocalData_.accountTagUpdate(callbackIten['data'])

    except KeyboardInterrupt:
        pass
    # Optional disconnect. If keeping an open connection to the input don't disconnet
    logging.info("Salimos como cobardes..")
    app.disconnect()
    
if __name__ == '__main__':
    main()
