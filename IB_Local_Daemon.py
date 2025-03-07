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
import IB_API_Client
import strategiesNew2
import webFE.webFENew_App
import os
import utils
import queue
from alarmManager import alarmManagerG

from dotenv import load_dotenv

loop_timer = 0.1


def SetupLogger():
    if not os.path.exists("log"):
        os.makedirs("log")

    
    try:
        max_len = str(utils.getLongestFileName())
    except:
        max_len = '25'

    time.strftime("pyibapi.%Y%m%d_%H%M%S.log")

    #recfmt = '(%(threadName)s) %(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s'
    recfmt = '%(asctime)s.%(msecs)03d %(levelname)-7s [%(filename)-MMMM.MMMMs:%(lineno)-4.4d] %(message)s'
    recfmt = recfmt.replace('MMMM', max_len)

    timefmt = '%y-%m-%d_%H:%M:%S'

    # logging.basicConfig( level=logging.DEBUG,
    #                    format=recfmt, datefmt=timefmt)
    filenameToday = "log/ibapi_sic.%y%m%d.log"
    path = 'log/'
    pathOld = 'log/old/'
    for i in sorted(os.listdir(path), reverse=True):
        filename = os.path.join(path,i)
        if os.path.isfile(filename) and i.startswith('ibapi_sic'):
            if filename != time.strftime(filenameToday):
                filename_mv = os.path.join(pathOld,i)
                os.rename(filename, filename_mv)

    logging.basicConfig(filename=time.strftime(filenameToday),
                        filemode="a",
                        level=logging.INFO,
                        format=recfmt, datefmt=timefmt)
    logger = logging.getLogger()              # El root looger afecta a todos los demas
    logger.setLevel(logging.INFO)

def webFE_loop(_mode):

    if _mode == 'Lab':
        port_ = 5500
    elif _mode == 'Prod':
        port_ = 5000
    else:
        port_ = 5500
    webFE.webFENew_App.appDashFE_.run_server(port=port_, debug=False, threaded=True, host= '0.0.0.0')

def reconnect_loop (app):

    max_con_fails = 0
    
    while True:
        if isinstance(app.nextorderId, int):
            logging.info("Conectado con TWS")
            alarmManagerG.clear_alarma(1001)
            break
        else:
            alarmManagerG.add_alarma({'code':1001})
            if max_con_fails == 0:
                logging.info("Waiting for connection...")
            max_con_fails += 1
            # LLegado cierto momento se podría hacer algo con t_api_thread
            if max_con_fails > 6:
                logging.info("Demasiado tiempo esperando. Reconectando.......")
                max_con_fails = 0
                app.reconnect()
            time.sleep(10) 

def main():
    load_dotenv()
    _mode = os.getenv('MODE')

    print ('Empezamos')
    
    SetupLogger()
    logging.info ('')
    logging.info ('')
    logging.info ('')
    logging.info ('')
    logging.info ("###########################################")
    logging.info ('# IB RODSIC (c) 2022  ')
    logging.info ('#')
    logging.info ("# Hora actual: %s", datetime.datetime.now())
    logging.info ('#')

    #globales.G_RTlocalData_ = None
    app = None
    #wsServer1 = None
    strategyIns = None 

    # Parsing Parameters
    
    cmdLineParser = argparse.ArgumentParser("api tests")
    cmdLineParser.add_argument("-b", "--brief", action="store_true", default=False, help="Only brief prints")

    args = cmdLineParser.parse_args()
    
    # Init de RT_LocalData
    
    globales.G_RTlocalData_.verboseBrief = args.brief
    
    # Init de IB_API_Client
    
    client_id = 0
    if _mode == 'Lab':
        _port = 4004
        _host = 'lab_ib_gateway'
    elif _mode == 'Prod':
        _port = 4003 # En realidad es 4001 para prod, pero socat me lo pasa a 4003
        _host = 'prod_ib_gateway'
        logging.info ('# SISTEMA EN PRODUCCION !!!!!')
    else:
        _port = 4004 # En realidad es 4001 para prod
        _host = 'lab_ib_gateway'

    logging.info ('#')
    logging.info ('Abriendo conexion con %s:%d', _host, _port)

    #####################
    #
    # El orden es el siguiente:
    #   0.- RT es global
    #   1.- app de API
    #   2.- Los web servers, pero pueden ir despues
    #   3.- Esperamos a confirmar conexion
    #   4.- Cargar Estrategias. Para que cuando arranquemos Orders ya estén, y se pueda actualizar la estrategia.
    #   5.- Pedimos posiciones, ordenes y accountInfo
    #   6.- Esperamos a tener toda la info de lo anterior
    #   7.- Procesamos Ordenes y AccountInfo
    #   8.- Pedimos a las estrategia que registren la ordenes que usan
    #   9.- Cargamos watchlist de contratos
    #   10.- Loop:
    #       1º  Miramos como esta la conexion entre este python y TWS
    #       2º. Miramos si las ordenes estan pilladas
    #       3º. Miramos si las posiciones estan bien
    #       4º. Miramos si los contratos estan bien
    #       5º. Miramos si nos hemos recuperado de algo
    #       6º. Miramos si las estrategias estan bien
    #       7º. Gestionamos la cola Prio
    #       8º. Gestionamos la cola Normal
    #       9º. Gestionamos si cargamos los compPrices
    #       10º. Gestionamos si cargamos los Prices


    # app.run()
    app = IB_API_Client.IBI_App(_host, _port, client_id, globales.G_RTlocalData_)
    #t_api_thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    #t_api_thread = threading.Thread(target=app.run, daemon=True)
    #t_api_thread.start()
    
    # Init web page
    #webFE1 = webFE.webFE(globals.G_RTlocalData_)
    t_webFE = threading.Thread(name='webFE', target=webFE_loop, args=(_mode,))
    t_webFE.start()

    # Init de wsServer
    #wsServer1 = wsServer.wsServer(app, globales.G_RTlocalData_)
    #t_wsServerIB = threading.Thread(name='wsServerIB', target=wsServer_loop, args=(wsServer1,_mode,))
    #t_wsServerIB.start()

    # Esperamos que esté conectado

    reconnect_loop (app)

    '''

    max_con_fails = 0
    
    while True:
        if isinstance(app.nextorderId, int):
            logging.info("Conectado con TWS")
            break
        else:
            if max_con_fails == 0:
                logging.info("Waiting for connection...")
            max_con_fails += 1
            # LLegado cierto momento se podría hacer algo con t_api_thread
            if max_con_fails > 6:
                logging.info("Demasiado tiempo esperando. Reconectando.......")
                max_con_fails = 0
                app.reconnect()
            time.sleep(10)    
    '''

    time.sleep (3)
    logging.info("Conexion establecida con TWS.")

    strategyIns = strategiesNew2.Strategies(globales.G_RTlocalData_, app)

    #assigning the return from our clock method to a variable 
    requested_time = app.server_clock()

    time_p = datetime.datetime.fromtimestamp( requested_time )
    logging.info("Hora de IB: %s", time_p)
    logging.info("Hora local: %s", datetime.datetime.now())

    app.reqAutoOpenOrders(True)
    app.reqPositions()    
    app.reqAllOpenOrders()
    app.reqAccountSummary(9001, "All", app.accSumTags.AllTags)
    app.reqMarketDataType(3)

    while True:
        if app.initOrders_ and app.initPositions_ and app.initAccount_:
            app.initReady_ = True
            logging.info("Ya hemos recibido toda la info inicial. Ahora hay que procesarlo")
            break
        else:
            logging.info("Esperando lista inicial de ordenes y posiciones")
            time.sleep(1)   

    # Hemos recibido todas las ordenes, y están en la lista. 
    # Necesito que se procesen, y así tengo todos los datos en RT para poder seguir bie 
    # 

    TempQueue = queue.Queue()   # Creo una cola intermedia

    while app.CallbacksQueuePrio_.empty() == False:
        callbackItem = app.CallbacksQueuePrio_.get()
        if 'type' not in callbackItem:
            continue
        elif callbackItem['type'] == 'order':
            bChange = globales.G_RTlocalData_.orderUpdate(callbackItem['data']) # Me dice si hay cambio o no
            # Añadir algo que actualizar ordenes en Strategy
            if bChange:
                strategyIns.strategyIndexOrderUpdate (callbackItem['data'])
        elif callbackItem['type'] == 'account':
            globales.G_RTlocalData_.accountTagUpdate(callbackItem['data'])
        else:
            TempQueue.put(callbackItem)
    
    app.CallbacksQueuePrio_ = TempQueue

    # Le decimos a las estrategias que pongan en RT cuales son sus ordenes
    strategyIns.strategySubscribeOrdersInit()

    # En este punto, toas las ordened, posiciones y AccountInfo ha sido tratado
    # Queda el resto que es menos importante

    logging.info("#############")
    logging.info("#############")
    logging.info("Ya hemos procesado toda la info inicial.")
    logging.info("#")
    logging.info("#")

    # Cargamos los contratos de la watchlist y fin.
                               
    logging.info("Cargando los contratos de la watchlist....")
    globales.G_RTlocalData_.contractLoadFixedWatchlist()
    logging.info("Cargados los contratos de la watchlist.")
    logging.info("#")
    logging.info("Listo para operar. Entramos en el loop......")
    logging.info("#")
    
    ###########################################
    # Loop Principal
    # 1º miramos como esta la conexion entre este python y TWS
    # 2º. Miramos si las ordenes estan pilladas
    # 3º. Miramos si las posiciones estan bien
    # 4º. Miramos si los contratos estan bien
    # 5º. Miramos si nos hemos recuperado de algo
    # 6º. Miramos si las estrategias estan bien
    # 7º. Gestionamos la cola Prio
    # 8º. Gestionamos la cola Normal
    # 9º. Gestionamos si cargamos los compPrices
    # 10º. Gestionamos si cargamos los Prices

    last_refresh_DB_time = datetime.datetime.now()
    last_refresh_DBcomp_time = datetime.datetime.now()
    try:
        while True:
            time.sleep(loop_timer)
            ahora = datetime.datetime.now()

            # 1º miramos como esta la conexion entre este python y TWS
            connState = app.check_connection_TWS()

            if connState == 1:
                logging.error('Error en la conexion con TWS. Desconectado')
                logging.error('Error en la conexion con TWS. Vamos a reconctar....')
                time.sleep(10)
                app.initOrders_ = False
                app.initPositions_ = False
                reconnect_loop (app)
                continue

            if connState == 2:
                logging.error('Error en la conexion con TWS. Conecting...')
                continue

            # 2º. Miramos si las ordenes estan pilladas
            if app.initOrders_ == False:  # Conectado pero sin ordenes
                app.initReady_ = False
                # Primero hay que borrar la lista actual por si se han cerrado o cancelado ordenes
                #globales.G_RTlocalData_.orderDeleteAll()
                try:
                    app.reqAllOpenOrders()
                except:
                    logging.error('Error en el loop con reqAllOpenOrders', exc_info=True)
                continue # Que no continue si initOrders_ == False

            # 3º. Miramos si las posiciones estan bien:
            if app.initPositions_ == False:
                app.initReady_ = False
                # Primero hay que borrar la lista actual por si se han cerrado o cancelado ordenes
                #globales.G_RTlocalData_.positionDeleteAll()
                try:
                    app.reqPositions()
                except:
                    logging.error('Error en el loop con reqPositions', exc_info=True)
                continue # Que no continue si initPositions_ == False

            # 4º. Miramos si los contratos estan bien:
            try:
                contratosIncompletos = globales.G_RTlocalData_.contractCheckStatus()  # Ver si los BAGs tienen sus legs completas
                                                                                      # Y ver si tenemos todos los simbolos y subscripcion a tick
            except:
                logging.error('Error en el loop con contractCheckStatus', exc_info=True)

            if contratosIncompletos == True:
                app.initReady_ = False
                try:
                    globales.G_RTlocalData_.contractReqDetailsAllMissing()
                except:
                    logging.error('Error en el loop con contractReqDetailsAllMissing', exc_info=True)
                continue

            # 5º. Miramos si nos hemos recuperado de algo:
            if app.initReady_ == False:         # Si aqui está False, es que hemos recuperado
                app.initReady_ = True             # Si llegamos aquí es que todo bien
                try:
                    globales.G_RTlocalData_.contractLoadFixedWatchlist()
                except:
                    logging.error('Error en el loop con contractLoadFixedWatchlist', exc_info=True)
                continue

            # 6º. Miramos si las estrategias estan bien:
            try:
                strategyIns.strategyIndexCheckAll() # Compruebo las strategias
            except:
                logging.error('Error en el loop con strategyIndexCheckAll', exc_info=True)

            # 7º. Gestionamos la cola Prio:
            while app.CallbacksQueuePrio_.empty() == False:
                callbackItem = app.CallbacksQueuePrio_.get()
                if 'type' not in callbackItem:
                    continue
                if callbackItem['type'] == 'execution':
                    try:
                        globales.G_RTlocalData_.executionAnalisys (callbackItem['data'])
                    except:
                        logging.error('Error en el loop con executionAnalisys', exc_info=True)
                if callbackItem['type'] == 'commission':
                    try:
                        globales.G_RTlocalData_.commissionAnalisys(callbackItem['data'])
                    except:
                        logging.error('Error en el loop con commissionAnalisys', exc_info=True)
                if callbackItem['type'] == 'order':
                    bChange = False
                    try:
                        bChange = globales.G_RTlocalData_.orderUpdate(callbackItem['data']) # Me dice si hay cambio o no
                    except:
                        logging.error('Error en el loop con orderUpdate', exc_info=True)
                    # Añadir algo que actualizar ordenes en Strategy
                    if bChange:
                        try:
                            strategyIns.strategyIndexOrderUpdate (callbackItem['data'])
                        except:
                            logging.error('Error en el loop con strategyIndexOrderUpdate', exc_info=True)
                if callbackItem['type'] == 'position':
                    try:
                        globales.G_RTlocalData_.positionUpdate (callbackItem['data'])
                    except:
                        logging.error('Error en el loop con positionUpdate', exc_info=True)
                if callbackItem['type'] == 'account':
                    try:
                        globales.G_RTlocalData_.accountTagUpdate(callbackItem['data'])
                    except:
                        logging.error('Error en el loop con accountTagUpdate', exc_info=True)
                if callbackItem['type'] == 'error':
                    if callbackItem['data'] == 10197:
                        try:
                            globales.G_RTlocalData_.dataFeedSetState(False)
                        except:
                            logging.error('Error en el loop con dataFeedSetState', exc_info=True)

            # 8º. Gestionamos la cola Normal:
            ahora = datetime.datetime.now()
            while app.CallbacksQueue_.empty() == False:
                callbackItem = app.CallbacksQueue_.get()
                if 'type' not in callbackItem:
                    continue
                if callbackItem['type'] == 'tick':
                    try:
                        globales.G_RTlocalData_.tickUpdatePrice (callbackItem['data'])
                    except:
                        logging.error('Error en el loop con tickUpdatePrice', exc_info=True)
                if callbackItem['type'] == 'pnl':
                    try:
                        globales.G_RTlocalData_.pnlUpdate (callbackItem['data'])
                    except:
                        logging.error('Error en el loop con pnlUpdate', exc_info=True)
                if (datetime.datetime.now() - ahora > datetime.timedelta(milliseconds=500)):
                    break


            # 9º. Gestionamos si cargamos los compPrices
            ahora = datetime.datetime.now()
            if (ahora - last_refresh_DBcomp_time > datetime.timedelta(minutes=15)):
                last_refresh_DBcomp_time = ahora
                try:
                    globales.G_RTlocalData_.contractReloadCompPrices()
                except:
                    logging.error('Error en el loop con contractReloadCompPrices', exc_info=True)

            # 10º. Gestionamos si cargamos los Prices
            ahora = datetime.datetime.now()
            if (ahora - last_refresh_DB_time > datetime.timedelta(minutes=5)):
                last_refresh_DB_time = ahora
                try:
                    dataFeedState = globales.G_RTlocalData_.dataFeedGetState()
                except:
                    logging.error('Error en el loop con dataFeedGetState', exc_info=True)
                if dataFeedState == False:
                    try:
                        globales.G_RTlocalData_.contractReloadPrices()
                    except:
                        logging.error('Error en el loop con contractReloadPrices', exc_info=True)

    except KeyboardInterrupt:
        pass
    # Optional disconnect. If keeping an open connection to the input don't disconnet
    logging.info("Salimos como cobardes..")
    app.disconnect()
    
if __name__ == '__main__':
    main()
