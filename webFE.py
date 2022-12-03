from flask import Flask
from dash import Dash, html, dcc, MATCH, ALL, Input, Output, State, ctx, no_update, dash
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import globales
import logging
import random


logger = logging.getLogger(__name__)


appDashFE_ = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])

appDashFE_.title = "IB RODSIC"

#####################################################################################################################
#####################################################################################################################
## Utils

def formatCurrency (cantidad):
    thousands_separator = "."
    fractional_separator = ","
    
    try:
        currency = "${:,.2f}".format(cantidad)
    except:
        logging.error ('La cantidad de dinero no es correcta')
        return None
    
    if thousands_separator == ".":
        if '.' in currency:
            main_currency, fractional_currency = currency.split(".")[0], currency.split(".")[1]
        else:
            main_currency = currency
        new_main_currency = main_currency.replace(",", ".")
        if '.' in currency:
            currency = new_main_currency + fractional_separator + fractional_currency
        else:
            currency = new_main_currency
    
    return (currency)

#####################################################################################################################
#####################################################################################################################
## Ordenes

def layout_ordenes_tab ():
    data = globales.G_RTlocalData_.orderReturnListAll()
    ContentItems = []
    item = 0
    #################################
    # Preparacion de Tab de ordenes
    for orden in data:
        
        random_wait = random.randint(0,2000) + 4000
        headerRowInn = ordenesObtenerFilas (orden, False)

        lOrderId = orden['order'].orderId
        
        headerRow = html.Div(
            [
                html.Div(
                    headerRowInn, id ={'role':'orden_header', 'orderId': str(lOrderId)}
                ),
                dcc.Interval(
                    id={'role': 'IntervalOrdersLine', 'orderId': str(lOrderId)},
                    interval= random_wait, # in milliseconds
                    n_intervals=0
                )
            ]
        )

        lorderType = orden['order'].orderType
        lPermId = str(orden['order'].permId)
        lgConId = str(orden['contractId'])
        lLmtPrice = orden['order'].lmtPrice
        if lorderType == 'STP':
            lLmtPrice = orden['order'].auxPrice
        lTif = orden['order'].tif

        lLmtPrice = formatCurrency (lLmtPrice)

        insideDetailsData = []
        insideDetailsData.append(html.Div(children = "gConId: " + lgConId, style = {"margin-left": "40px"}))
        insideDetailsData.append(html.Div(children = "PermId: " + lPermId, style = {"margin-left": "40px"}))
        insideDetailsData.append(html.Div(children = "Order Type: " + lorderType, style = {"margin-left": "40px"}))
        insideDetailsData.append(html.Div(children = "Limit Price: " + lLmtPrice, style = {"margin-left": "40px"}))
        insideDetailsData.append(html.Div(children = "Time in Force: " + lTif, style = {"margin-left": "40px"}))

        collapseDetails = dbc.Collapse(
            dbc.Row(
                [
                    dbc.Col(insideDetailsData),
                ],
            ),
            id={'role': 'colapse', 'index': lOrderId},
            is_open=False,
            
        )
        
        random_wait = random.randint(0,2000) + 4000
        intervalDiv = dcc.Interval(
            id={'role': 'IntervalOrdersLine', 'orderId': lOrderId},
            interval= random_wait, # in milliseconds
            n_intervals=0
        )


        ContentItems.append({"header": headerRow, "details": collapseDetails})
        item += 1

    #################################
    # Ahora creamos el tab de ordenes usando la info anterior

    #dbc.Input(id={'role': 'ZoneInputDown', 'strategySymbol': symbol, 'index': itemZG}, value=val2, type="text", debounce=True, readonly= True, className="text-end")
    tabOrdenes = [
            dbc.Row(
                dbc.Col(html.H1("Lista de Ordenes",
                                className='text-center text-primary mb-4'),
                        width=12)
            ),
            dbc.Row(
                [
                    dbc.Col(html.Div("OrdenId"), className = 'bg-primary mr-1', width = 1),
                    dbc.Col(html.Div("Symbol"), className = 'bg-primary mr-1', width = 3),
                    dbc.Col(html.Div("Action"), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("Status"), className = 'bg-success', width = 1),
                    dbc.Col(html.Div("Fill Status"), className = 'bg-primary', width = 2),
                    dbc.Col(html.Div("LastFill"), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("Comment"), className = 'bg-primary', width = 2),
                    dbc.Col(html.Div("Cancel"), className = 'bg-primary', width = 1),
                ], className = 'mb-3 text-white'
                ),
            ]

    for line in ContentItems:
      
        tabOrdenes.append(line['header'])
        tabOrdenes.append(line['details'])

    return tabOrdenes

#####################################################################################################################
#####################################################################################################################
## Contratos

def layout_contratos_tab ():

    data = globales.G_RTlocalData_.contratoReturnDictAll()
    ContentItems = []
    item = 0
    #################################
    # Preparacion de Tab de contratos
    for gConId, contrato in data.items():
        #posicion = globales.G_RTlocalData_.positionGetByGconId(contrato['gConId'])  #cambiar con nuevo RT
        posicion = contrato['pos']
        
        insideDetailsData = []
        if posicion == None:
            posQty = 0
            posavgCost = 0
        else:
            posQty = formatCurrency(posicion) 
            posavgCost = formatCurrency(contrato['posAvgPrice'])
        priceBuy = formatCurrency(contrato['currentPrices']['BUY'])
        priceSell = formatCurrency(contrato['currentPrices']['SELL'])
        priceLast = formatCurrency(contrato['currentPrices']['LAST'])
        symbol = contrato['fullSymbol']
        #symbol = globales.G_RTlocalData_.contractSummaryBrief(contrato['gConId'])
        # Cada fila de cabecera
        headerRow = dbc.Row(
                [
                    dbc.Col(dbc.Button(symbol,id={'role': 'boton', 'index': item}), className = 'bg-primary mr-1', width = 4),
                    dbc.Col(html.Div(posQty), className = 'bg-primary mr-1', width = 1),
                    dbc.Col(html.Div(posavgCost), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div(priceBuy), className = 'bg-success', width = 1),
                    dbc.Col(html.Div(priceSell), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div(priceLast), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("Comment"), className = 'bg-primary', width = 3),
                ], className = 'text-white mb-1',
        )        
        # Los detalles que se ocultan. Dos columnas, detalles y figura 
        # Primero los detalles
        insideDetailsData.append(html.Div(children = "ConId: " + str(contrato['contract'].conId), style = {"margin-left": "40px"}))
        insideDetailsData.append(html.Div(children = "Symbol: " + str(contrato['contract'].localSymbol), style = {"margin-left": "40px"}))
        insideDetailsData.append(html.Div(children = "secType: " + str(contrato['contract'].secType), style = {"margin-left": "40px"}))
        if contrato['contract'].secType == "BAG":
            for leg in contrato['contract'].comboLegs:
                insideDetailsData.append(html.Div(children = "Leg: ", style = {"margin-left": "40px"}))
                insideDetailsData.append(html.Div(children = "ConId: " + str(leg.conId), style = {"margin-left": "80px"}))
                insideDetailsData.append(html.Div(children = "Action: " + str(leg.action), style = {"margin-left": "80px"}))
                insideDetailsData.append(html.Div(children = "Ratio: " + str(leg.ratio), style = {"margin-left": "80px"}))

                insideDetailsData.append(html.Div(children = "LocalSymbol: " + data[leg.conId]['contract'].localSymbol, style = {"margin-left": "80px"}))
                insideDetailsData.append(html.Div(children = "LastOrderDate: " + data[leg.conId]['contract'].lastTradeDateOrContractMonth, style = {"margin-left": "80px"}))
                '''
                for contratoLeg in data:
                    if contratoLeg['contract'].conId == leg.conId:
                        insideDetailsData.append(html.Div(children = "LocalSymbol: " + contratoLeg['contract'].localSymbol, style = {"margin-left": "80px"}))
                        insideDetailsData.append(html.Div(children = "LastOrderDate: " + contratoLeg['contract'].lastTradeDateOrContractMonth, style = {"margin-left": "80px"}))
                        break
                '''
        elif contrato['contract'].secType == "FUT":
            insideDetailsData.append(html.Div(children = "Date: " + str(contrato['contract'].lastTradeDateOrContractMonth), style = {"margin-left": "40px"}))

        # El grafico
        #fig = px.line(contrato['dbPandas'].dbGetDataframe(), x="timestamp", y="LAST", title="LAST Evolution") 
        #fig.update_layout(xaxis = dict(type="category")) # Para que no deje los vacios de fecha de cierre
        df_today = contrato['dbPandas'].dbGetDataframeToday()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_today['timestamp'], y=df_today["LAST"], mode="lines", connectgaps = True))
        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
                dict(bounds=[20.25, 14.5], pattern="hour"),  # hide hours outside of 9.30am-4pm
                #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
            ]
        )
        graphColumn = html.Div(
            dcc.Graph(
                    id={'role': 'graphDetails', 'index': item},
                    figure = fig 
            )
        )
        # Todo lo que se oculta junto
        collapseDetails = dbc.Collapse(
            dbc.Row(
                [
                    dbc.Col(insideDetailsData, width = 5),
                    dbc.Col(graphColumn, width = 7),
                ],
            ),
            id={'role': 'colapse', 'index': item},
            is_open=False,
        )

        ContentItems.append({"header": headerRow, "details": collapseDetails})
        item += 1

    #################################
    # Ahora creamos el tab de contratos usando la info anterior
    tabContratos = [
            dbc.Row(
                dbc.Col(html.H1("Lista de Contratos",
                                className='text-center text-primary mb-4'),
                        width=12)
            ),
            dbc.Row(
                [
                    dbc.Col(html.Div("Symbol"), className = 'bg-primary mr-1', width = 4),
                    dbc.Col(html.Div("Pos"), className = 'bg-primary mr-1', width = 1),
                    dbc.Col(html.Div("AvgPrice"), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("Buy"), className = 'bg-success', width = 1),
                    dbc.Col(html.Div("Sell"), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("Last"), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("Comment"), className = 'bg-primary', width = 3),
                ], className = 'mb-3 text-white'
                ),
            ]

    for line in ContentItems:
      
        tabContratos.append(line['header'])
        tabContratos.append(line['details'])

    return tabContratos

#####################################################################################################################
#####################################################################################################################
## Estrategias

def layout_strategies_tab():
    #contracts_ = globales.G_RTlocalData_.contratoReturnListAll()
    #strategiesIndex_ = globales.G_RTlocalData_.strategies_.strategyIndexGetAll()
    strategyMariposaVerano_ = globales.G_RTlocalData_.strategies_.strategyPentagramaObj_.strategyPentagramaGetAll()
    #{'symbol': lineSymbol, 'currentPos': lineCurrentPos, 'UpperOrderId': lineUpperOrderId, 'UpperOrderPermId': lineUpperOrderPermId, 'LowerOrderId': lineLowerOrderId, 'LowerOrderPermId': lineLowerOrderPermId, 'zones': zones}

    item = 0
    itemZG = 0 # Sirve para dar identidades unicas a las zonas
    ContentItems = []
    ####################################
    # Preparacion de Tab de Estratgias
    for estrategia in strategyMariposaVerano_:
        symbol = estrategia['symbol']
        
        random_wait = random.randint(0,2000) + 4000
        headerRowInn = layout_getStrategyHeader (estrategia, False)
        
        headerRow = html.Div(
            [
                html.Div(
                    headerRowInn, id ={'role':'estrategia_header', 'symbol': symbol}
                ),
                dcc.Interval(
                    id={'role': 'IntervalHeaderStrategy', 'symbol': symbol},
                    interval= random_wait, # in milliseconds
                    n_intervals=0
                )
            ]
        )



        # Los dos graficos
        fig1 = layout_getFigureHistorico(estrategia)   # Lo tengo en una funcion para que sea facil actualizar
        graphColumn1 = html.Div(
            dcc.Graph(
                    id={'role': 'graphDetailsComp', 'strategySymbol': symbol},
                    animate = False,
                    figure = fig1
            )
        )
        
        random_wait = random.randint(0,1000) + 10000
        fig2 = layout_getFigureToday(estrategia, False)   # Lo tengo en una funcion para que sea facil actualizar
        graphColumn2 = html.Div([
            dcc.Graph(
                    id={'role': 'graphDetailsToday', 'strategySymbol': symbol},
                    animate = False,
                    figure = fig2
            ),
            dcc.Interval(
                id={'role': 'IntervalgraphToday', 'strategySymbol': symbol},
                interval= random_wait, # in milliseconds
                n_intervals=0
            )
        ])
        
        # Los detalles de la estrategia (escondidos)

        # Primero las zonas con sus datos
        
        zonasFilaHeader = []
        zonasFilaBorderUp = []
        zonasFilaBorderDown = []
        zonasFilaPosiciones = []
        zonasFilaHeader.append(dbc.Col(''))
        zonasFilaBorderUp.append(dbc.Col('Limit Up', align="center"))
        zonasFilaBorderDown.append(dbc.Col('Limit Down', align="center"))
        zonasFilaPosiciones.append(dbc.Col('Posiciones', align="center"))
        itemZ = 1
        for zone in estrategia['zonesNOP']:
            val1 = zone['limitUp']
            val2 = zone['limitDown']
            val3 = zone['reqPos']
            
            zonasFilaHeader.append(dbc.Col('Zona ' + str(itemZ), className="text-center"))
            zonasFilaBorderUp.append(dbc.Col(dbc.Input(id={'role': 'ZoneInputUp', 'strategySymbol': symbol, 'index': itemZG}, value=val1, type="text", debounce=True, className="text-end")))
            if itemZ < len(estrategia['zonesNOP']):
                zonasFilaBorderDown.append(dbc.Col(dbc.Input(id={'role': 'ZoneInputDown', 'strategySymbol': symbol, 'index': itemZG}, value=val2, type="text", debounce=True, readonly= True, className="text-end")))
            else:
                zonasFilaBorderDown.append(dbc.Col(dbc.Input(id={'role': 'ZoneInputDown', 'strategySymbol': symbol, 'index': itemZG}, value=val2, type="text", debounce=True, readonly= False, className="text-end")))
            zonasFilaPosiciones.append(dbc.Col(dbc.Input(id={'role': 'ZoneInputPos', 'strategySymbol': symbol, 'index': itemZG}, value=val3, type="text", debounce=True, className="text-end")))
            itemZ += 1
            itemZG += 1

        insideDetailsZonas = []
        insideDetailsZonas.append(dbc.Row(zonasFilaHeader))
        insideDetailsZonas.append(dbc.Row(zonasFilaBorderUp))
        insideDetailsZonas.append(dbc.Row(zonasFilaBorderDown, id={'role': 'filaZoneDown', 'strategySymbol': symbol}))
        insideDetailsZonas.append(dbc.Row(zonasFilaPosiciones))

        # Ahora los botones de Actualizar/Reset

        insideDetailsBotonesZonas = []
        insideDetailsBotonesZonas.append(dbc.Row(dbc.Button("Actualizar", id={'role': 'ZoneButtonSave', 'strategySymbol': symbol}, className="me-2", n_clicks=0)))
        insideDetailsBotonesZonas.append(dbc.Row(dbc.Button("Reset", id={'role': 'ZoneButtonReset', 'strategySymbol': symbol}, className="me-2", n_clicks=0)))

        # Y las tablas con ordenes

        insideTable = layout_getStrategyTableOrders(estrategia)
        
        random_wait = random.randint(0,2000) + 3000
        insideOrdenes = html.Div([
            html.Div(
                insideTable, 
                id={'role': 'TableStrategyOrderDetails', 'symbol': symbol},
            ),
            dcc.Interval(
                id={'role': 'IntervalOrderTable', 'symbol': symbol},
                interval= random_wait, # in milliseconds
                n_intervals=0
            )
        ])

        insideZonas = []
        insideZonas.append(dbc.Col(insideDetailsZonas, width=11))
        insideZonas.append(dbc.Col(insideDetailsBotonesZonas, width=1))
        #insideDetails.append(dbc.Col(insideDetailsOrdenes, width=6))
        # Todo lo que se oculta junto
        collapseDetails = dbc.Collapse(
            [
                dbc.Row(
                        insideOrdenes,
                ),
                dbc.Row(
                    [
                        dbc.Col(graphColumn1, width=6),
                        dbc.Col(graphColumn2, width=6)
                    ]
                ),
                dbc.Row(
                        insideZonas,
                )
            ],
            id={'role': 'colapse_strategy', 'symbol': symbol},
            is_open=False,
            className = 'mb-3'
        )
        item += 1   

        

        
        ContentItems.append({"header": headerRow, "details": collapseDetails})

    #################################
    # Ahora creamos el tab de estrategias usando la info anterior
    tabEstrategias = [
            dbc.Row(
                [
                    html.H1("Lista de Estrategias", className='text-left text-secondary mb-4 display-4'),
                    html.Hr()
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(html.Div("Symbol"), className = 'bg-primary mr-1', width = 4),
                    dbc.Col(html.Div("Pos"), className = 'bg-primary mr-1', width = 1),
                    dbc.Col(html.Div("dailyPnL"), className = 'bg-primary mr-1', width = 1),
                    dbc.Col(html.Div("realizedPnL"), className = 'bg-primary mr-1', width = 1),
                    dbc.Col(html.Div("unrealizedPnL"), className = 'bg-primary mr-1', width = 1),
                    dbc.Col(html.Div("Comment"), className = 'bg-primary', width = 3),
                    dbc.Col(html.Div("Enabled"), className = 'bg-primary', width = 1),
                ], className = 'mb-3 text-white'
                ),
            ]

    for line in ContentItems:
        tabEstrategias.append(line['header'])
        tabEstrategias.append(line['details'])

    return tabEstrategias

def layout_getFigureHistorico (estrategia):

    symbol = estrategia['symbol']
    contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
    if not contrato:
        logging.error ("Error cargando grafico historico de %s. No tenemos el contrato cargado en RT_Data", symbol)
        return no_update
    df_comp = contrato['dbPandas'].dbGetDataframeComp()
    fig1 = go.Figure()
    fig1.add_trace(go.Candlestick(x=df_comp.index, open=df_comp['open'], high=df_comp['high'],low=df_comp['low'],close=df_comp['close']))
    limitList= []
    for zone in estrategia['zonesNOP']:       
        if zone['limitUp'] not in limitList:
            zoneborder = [zone['limitUp']] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_color="gray", line_width=1, connectgaps = True, fill=None))
            limitList.append(zone['limitUp'])
        if zone['limitDown'] not in limitList:
            zoneborder = [zone['limitDown']] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_color="gray", line_width=1, connectgaps = True, fill=None))
            limitList.append(zone['limitDown'])
    fig1.update_layout(showlegend=False, 
                       xaxis_rangeslider_visible=False, 
                       title_text='Historico (15min)', 
                       title_x = 0.5,
                       title_xanchor = 'center')
    
    fig1.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
            dict(bounds=[20.25, 15.66], pattern="hour"),  # hide hours outside of 9.30am-4pm
            #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
        ]
    )

    return fig1



def layout_getFigureToday (estrategia, update = False):
    symbol = estrategia['symbol']
    contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
    if not contrato:
        logging.error ('Error cargando grafico de Hoy de %s. No tenemos el contrato cargado en RT_Data', symbol)
        return no_update
    if (contrato['dbPandas'].toPrint == False) and (update == True):
        logging.debug ('Grafico no actualizado. No hay datos nuevos')
        return no_update
    dfToday = contrato['dbPandas'].dbGetDataframeToday()
    fig2 = go.Figure()

    #highlight de la zona actual y precios
    price_Upper = estrategia['lastCurrentZoneBufferPriceUp']
    price_Lower = estrategia['lastCurrentZoneBufferPriceDown']
    if price_Upper != None and price_Lower != None:
        zoneborder = [price_Upper] * len (dfToday.index)
        fig2.add_trace(go.Scatter(x=dfToday["timestamp"], 
                                  y=zoneborder, 
                                  mode="lines", 
                                  line_color="blue", 
                                  line_width=1, 
                                  connectgaps = True, 
                                  fill='none'))
    
        zoneborder = [price_Lower] * len (dfToday.index)
        fig2.add_trace(go.Scatter(x=dfToday["timestamp"], 
                                  y=zoneborder, 
                                  mode="lines", 
                                  line_color="blue", 
                                  line_width=1, 
                                  connectgaps = True, 
                                  fillcolor='rgba(0, 0, 255, 0.1)',    #azure = 240, 255, 255
                                  fill='tonexty'))

    # Valores de LAST
    fig2.add_trace(go.Scatter(x=dfToday['timestamp'], y=dfToday["BID"], mode="lines", line_color="blue", connectgaps = True))
    fig2.add_trace(go.Scatter(x=dfToday['timestamp'], y=dfToday["ASK"], mode="lines", line_color="crimson", connectgaps = True))
    
    # Y las zonas
    limitList= []
    nZone = 0
    for zone in estrategia['zonesNOP']:       
        if zone['limitUp'] not in limitList:
            zoneborder = [zone['limitUp']] * len (dfToday.index)
            fig2.add_trace(go.Scatter(x=dfToday["timestamp"], 
                                      y=zoneborder, 
                                      mode="lines", 
                                      line_color="gray", 
                                      line_width=1, 
                                      connectgaps = True, 
                                      fill='none'))
            limitList.append(zone['limitUp'])
        if zone['limitDown'] not in limitList:
            zoneborder = [zone['limitDown']] * len (dfToday.index)
            fig2.add_trace(go.Scatter(x=dfToday["timestamp"], 
                                      y=zoneborder, 
                                      mode="lines", 
                                      line_color="gray", 
                                      line_width=1, 
                                      connectgaps = True, 
                                      fill='none'))
            limitList.append(zone['limitDown'])
        nZone += 1

    fig2.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
            dict(bounds=[20.25, 15.16], pattern="hour"),  # hide hours outside of 9.30am-4pm
            #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
        ]
    )

    rannn = str(random.randint(0,1000))
    logging.info ('Grafico actualizado con %s', rannn)
    fig2.update_layout(showlegend=False, 
                       title_text='Datos Tiempo Real Hoy', 
                       title_x = 0.5,
                       title_xanchor = 'center')

    contrato['dbPandas'].toPrint = False

    return fig2

def layout_getStrategyHeader (estrategia, update = False):
    
    symbol = estrategia['symbol']
    posQty = estrategia['currentPos']
    stratEnabled = estrategia['stratEnabled']
    contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
    if not contrato:
        logging.error ('Error cargando estrategia Headerde %s. No tenemos el contrato cargado en RT_Data', symbol)
        return no_update
    if (contrato['dbPandas'].toPrintPnL == False) and (update == True):
        logging.debug ('Header estrategia no actualizado. No hay datos nuevos')
        return no_update

    dailyPnL = ''
    realizedPnL = ''
    unrealizedPnL = ''
    if contrato != None:
        lastPnL = contrato['dbPandas'].dbGetLastPnL()
        if lastPnL['dailyPnL'] != None:
            dailyPnL = formatCurrency(lastPnL['dailyPnL'])
        if lastPnL['realizedPnL'] != None:
            realizedPnL = formatCurrency(lastPnL['realizedPnL'])
        if lastPnL['unrealizedPnL'] != None:
            unrealizedPnL = formatCurrency(lastPnL['unrealizedPnL'])

    # Cabecera para cada contrato con estrategia
    
    headerRow = dbc.Row(
        [
            dbc.Col(dbc.Button(symbol,id={'role': 'boton_strategy_header', 'symbol': symbol}), className = 'bg-primary mr-1', width = 4),
            dbc.Col(html.Div(posQty), className = 'bg-primary mr-1', width = 1),
            dbc.Col(html.Div(dailyPnL), className = 'bg-primary mr-1', width = 1),
            dbc.Col(html.Div(realizedPnL), className = 'bg-primary mr-1', width = 1),
            dbc.Col(html.Div(unrealizedPnL), className = 'bg-primary mr-1', width = 1),
            dbc.Col(html.Div(""), className = 'bg-primary mr-1', width = 3),
            dbc.Col(dbc.Switch(id={'role': 'switchStratEnabled', 'symbol': symbol}, value = stratEnabled), className = 'bg-primary mr-1', width = 1),
        ], className = 'text-white mb-1'
    )
    
    contrato['dbPandas'].toPrintPnL = False
    return headerRow

def layout_getStrategyTableOrders (estrategia, update = False):

    #orden = globales.G_RTlocalData_.orderGetByOrderId(lOrderId)
    if estrategia['ordersUpdated'] == False and update == True:
        logging.debug ('Tabla de ordenes en Strategia no actualizado. No hay datos nuevos')
        return no_update

    ordenUp = globales.G_RTlocalData_.orderGetByOrderId (estrategia['UpperOrderId'])
    if ordenUp:
        posUp = ordenUp['order'].totalQuantity
        typeUp = ordenUp['order'].orderType
        if ordenUp['params'] != None and 'status' in ordenUp['params']:
            statusUp = ordenUp['params']['status']
        else:
            statusUp = 'N/A'
        lmtUp = ordenUp['order'].lmtPrice
        if ordenUp['order'].orderType == 'STP':
            lmtUp = ordenUp['order'].auxPrice
        if ordenUp['order'].action == 'SELL':
            posUp = posUp * (-1)
    else:
        posUp = 'N/A'
        lmtUp = 'N/A'
        typeUp = 'N/A'
        statusUp = 'N/A'
    
    ordenDown = globales.G_RTlocalData_.orderGetByOrderId (estrategia['LowerOrderId'])
    if ordenDown:
        posDown = ordenDown['order'].totalQuantity
        typeDown = ordenDown['order'].orderType
        if ordenDown['params'] != None and 'status' in ordenDown['params']:
            statusDown = ordenDown['params']['status']
        else:
            statusDown = 'N/A'
        lmtDown = ordenDown['order'].lmtPrice
        if ordenDown['order'].orderType == 'STP':
            lmtDown = ordenDown['order'].auxPrice
        if ordenDown['order'].action == 'SELL':
            posDown = posDown * (-1)
    else:
        posDown = 'N/A'
        lmtDown = 'N/A'
        typeDown = 'N/A'
        statusDown = 'N/A'
    

    insideDetailsTableHeader = [
        html.Thead(
            html.Tr(
                [
                   html.Th(""), 
                   html.Th("Order Id"),
                   html.Th("Perm Id"),
                   html.Th("Lmt"),
                   html.Th("Type"),
                   html.Th("Status"),
                   html.Th("Qty"),
                ]
            )   
        )
    ]

    insideDetailsTableRowUp = html.Tr(
        [
            html.Td("Orden Up"), 
            html.Td(str(estrategia['UpperOrderId'])),
            html.Td(str(estrategia['UpperOrderPermId'])),
            html.Td(str(lmtUp)),
            html.Td(str(typeUp)),
            html.Td(str(statusUp)),
            html.Td(str(posUp)),
        ]
    )

    insideDetailsTableRowDwn = html.Tr(
        [
            html.Td("Orden Down"), 
            html.Td(str(estrategia['LowerOrderId'])),
            html.Td(str(estrategia['LowerOrderPermId'])),
            html.Td(str(lmtDown)),
            html.Td(str(typeDown)),
            html.Td(str(statusDown)),
            html.Td(str(posDown)),
        ]
    )

    insideDetailsTableBody = [html.Tbody([insideDetailsTableRowUp, insideDetailsTableRowDwn])]
    estrategia['ordersUpdated'] = False

    ret = dbc.Table(
        insideDetailsTableHeader + insideDetailsTableBody, 
        bordered=True
    )

    return ret

def ordenesObtenerFilas (orden, update = False):
    #orden = globales.G_RTlocalData_.orderGetByOrderId(lOrderId)
    if orden == None or 'toPrint' not in orden:
        logging.debug ('Ordenes aun sin cargae')
        return no_update
    if orden['toPrint'] == False and update == True:
        logging.debug ('Header ordenes no actualizado. No hay datos nuevos')
        return no_update
    lOrderId = orden['order'].orderId
    lAction = orden['order'].action
    lQty = orden['order'].totalQuantity
    lStatus = orden['params']['status'] if 'status' in orden['params'] else ''
    lFilled = orden['params']['filled'] if 'filled' in orden['params'] else ''
    lRemaining = orden['params']['remaining'] if 'remaining' in orden['params'] else ''
    lLastFillPrice = orden['params']['lastFillPrice'] if 'lastFillPrice' in orden['params'] else ''
    symbol = globales.G_RTlocalData_.contractSummaryBrief(orden['contractId'])
    lFillState = str(lQty) + '/' + str(lFilled) + '/' + str(lRemaining)

    headerRow = dbc.Row(
            [
                dbc.Col(dbc.Button(str(lOrderId),id={'role': 'boton', 'index': lOrderId}), className = 'bg-primary mr-1', width = 1),
                dbc.Col(html.Div(symbol), className = 'bg-primary mr-1', width = 3),
                dbc.Col(html.Div(lAction), className = 'bg-primary', width = 1),
                dbc.Col(html.Div(lStatus), className = 'bg-success', width = 1),
                dbc.Col(html.Div(lFillState), className = 'bg-primary', width = 2),
                dbc.Col(html.Div(lLastFillPrice), className = 'bg-primary', width = 1),
                dbc.Col(html.Div("Comment"), className = 'bg-primary', width = 2),
                dbc.Col(dbc.Button(html.I(className="bi bi-x-circle me-2"),id={'role': 'boton_order_cancel', 'orderId': str(lOrderId)}), className = 'bg-primary', width = 1),
            ], className = 'text-white mb-1'
    )  
    orden['toPrint'] = False
    return headerRow

def modal_error():
    modal = html.Div(
        [
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Deafult", id = "modalErrorHeader")),
                    dbc.ModalBody("Default", id = "modalErrorBody"),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close", id="modal_boton_close", className="ms-auto", n_clicks=0
                        )
                    ),
                ],
                id="modal_error_main",
                is_open=False,
            ),
        ]
    )
    return modal


def layout_init():
    chil1 = [
        html.H1(
            children="Prueba Front-End IB",
            style={"textAlign": "center"}
        ),
    ]

    layout = html.Div(
        id="parent",
        children=chil1
    )
    #return layout
    if globales.G_RTlocalData_ == None:
        return layout

    if globales.G_RTlocalData_.appObj_ == None:
        return layout
        
    if globales.G_RTlocalData_.appObj_.initReady_ == False:
        return layout
    
    tabs = html.Div(
        [
            dbc.Tabs(
                [
                    dbc.Tab(label="Estrategias", tab_id="tab-estrat"),
                    dbc.Tab(label="Contratos", tab_id="tab-contrat"),
                    dbc.Tab(label="Ordenes", tab_id="tab-ordenes"),
                ],
                id="tabs",
                active_tab="tab-estrat",
            ),
            html.Div(id="tabContent"),
        ]
    )

    layout = dbc.Container(
        [
            tabs,
            modal_error(),

        ]
    )
    return layout

appDashFE_.layout = layout_init   # Sin parentesis para que pille la funcion, no el valor

# Callback para cambiar tab
@appDashFE_.callback(Output("tabContent", "children"), [Input("tabs", "active_tab")])
def switch_tab(at):
    if at == "tab-contrat":
        return layout_contratos_tab()
    elif at == "tab-estrat":
        return layout_strategies_tab()
    elif at == "tab-ordenes":
        return layout_ordenes_tab()
    return html.P("This shouldn't ever be displayed...")

# Callback para colapsar o mostrar filas Generico
@appDashFE_.callback(
    Output({'role': 'colapse', 'index': MATCH}, "is_open"),
    Input({'role': 'boton', 'index': MATCH}, "n_clicks"),
    State({'role': 'colapse', 'index': MATCH}, "is_open"),
    prevent_initial_call = True,
)
def toggle_colapse_generic(n_button, is_open):
    if n_button:
        return not is_open
    return is_open

# Callback para colapsar o mostrar filas Strategias
@appDashFE_.callback(
    Output({'role': 'colapse_strategy', 'symbol': MATCH}, "is_open"),
    Input({'role': 'boton_strategy_header', 'symbol': MATCH}, "n_clicks"),
    State({'role': 'colapse_strategy', 'symbol': MATCH}, "is_open"),
    prevent_initial_call = True,
)
def toggle_colapse_strategy(n_button, is_open):
    if n_button:
        return not is_open
    return is_open

#Callback para actualizar fila de valores de Ordenes
@appDashFE_.callback(
    Output({'role':'orden_header', 'orderId': MATCH}, "children"),
    Input({'role': 'IntervalOrdersLine', 'orderId': MATCH}, 'n_intervals'),
    prevent_initial_call = True,
)
def actualizarFilaOrdenes (n_intervals):
    if not ctx.triggered_id:
        raise PreventUpdate
    logging.debug ('Actualizando Ordenes Fila')
    orderId = ctx.triggered_id['orderId']
    try:
        orderId = int (orderId)
    except:
        logging.error ('Error en la ordenId al actualizar lista')
    orden = globales.G_RTlocalData_.orderGetByOrderId(orderId)
    resp = ordenesObtenerFilas (orden, True )
    return resp

#Callback para actualizar fila de valores de Strategies
@appDashFE_.callback(
    Output({'role':'estrategia_header', 'symbol': MATCH}, "children"),
    Input({'role': 'IntervalHeaderStrategy', 'symbol': MATCH}, 'n_intervals'),
    prevent_initial_call = True,
)
def actualizarFilaStrategies (n_intervals):
    if not ctx.triggered_id:
        raise PreventUpdate
    logging.debug ('Actualizando Estrategia Fila')
    symbol = ctx.triggered_id['symbol']

    estrategia = globales.G_RTlocalData_.strategies_.strategyPentagramaObj_.strategyPentagramaGetStrategyBySymbol (symbol)
    
    resp = layout_getStrategyHeader (estrategia, True)
    return resp

#Callback para actualizar tabla de ordenes en Strategy
@appDashFE_.callback(
    Output({'role':'TableStrategyOrderDetails', 'symbol': MATCH}, "children"),
    Input({'role': 'IntervalOrderTable', 'symbol': MATCH}, 'n_intervals'),
    prevent_initial_call = True,
)
def actualizarTablaOrdenesStrategies (n_intervals):
    if not ctx.triggered_id:
        raise PreventUpdate
    logging.debug ('Actualizando tabla ordenes estrategia')
    symbol = ctx.triggered_id['symbol']

    estrategia = globales.G_RTlocalData_.strategies_.strategyPentagramaObj_.strategyPentagramaGetStrategyBySymbol (symbol)
    
    resp = layout_getStrategyTableOrders (estrategia, True)
    return resp


# Callback para sincronizar limites de zona, definir limites
# Y actualizar graphs
@appDashFE_.callback(
    Output({'role': 'filaZoneDown', 'strategySymbol': MATCH}, "children"),
    Output({'role': 'graphDetailsComp', 'strategySymbol': MATCH}, 'figure'),
    Output({'role': 'graphDetailsToday', 'strategySymbol': MATCH}, 'figure'),
    Input({'role': 'ZoneInputUp', 'strategySymbol': MATCH, 'index': ALL}, "value"),
    Input({'role': 'ZoneInputDown', 'strategySymbol': MATCH, 'index': ALL}, "value"),
    Input({'role': 'ZoneInputPos', 'strategySymbol': MATCH, 'index': ALL}, "value"),
    Input({'role': 'IntervalgraphToday', 'strategySymbol': MATCH}, 'n_intervals'),
    prevent_initial_call = True,
)
def syncLimites(zoneUps, zoneDowns, zonePos, n_intervals):
    inputsUps = ctx.inputs_list[0]
    inputsDowns = ctx.inputs_list[1]
    inputsPos = ctx.inputs_list[2]

    if not ctx.triggered_id:
        raise PreventUpdate

    symbol = inputsUps[0]['id']['strategySymbol']  # Lo pillo de esta, pero da igual

    zonasFilaBorderDown = no_update

    intervalUpdate = True
    if ctx.triggered_id['role'] != 'IntervalgraphToday':
        intervalUpdate = False
        # Sincronizamos los border de filas entre ellos (upper de unos es lower de otros)
        zonasFilaBorderDown = []
        zonasFilaBorderDown.append(dbc.Col('Limit Down', align="center"))
        logging.info ('triggered_id %s', ctx.triggered_id)
        if 'role' in ctx.triggered_id:
            logging.info ('role %s', ctx.triggered_id['role'])
        logging.info ('triggered_prop_ids %s', ctx.triggered_prop_ids)
        for i in range(len(inputsDowns) -1):
            zoneD = inputsDowns[i]
            val = inputsUps[i+1]['value']
            inputsDowns[i]['value'] = val
            zonasFilaBorderDown.append(dbc.Col(dbc.Input(id=zoneD['id'], value=val, type="text", readonly= True, className="text-end")))
        zoneD = inputsDowns[-1]
        val = inputsDowns[-1]['value']
        zonasFilaBorderDown.append(dbc.Col(dbc.Input(id=zoneD['id'], value=val, type="text", readonly= False, className="text-end")))
    
        # Actualizamos la zonesNOP
        #zone = {'reqPos':pos), 'limitUp': float(limit_up), 'limitDown': float(limitdown)}
    
        lzones = []
        for i in range (len(inputsUps)):
            zone = {'reqPos':int(inputsPos[i]['value']), 'limitUp': float(inputsUps[i]['value']), 'limitDown': float(inputsDowns[i]['value'])}
            lzones.append(zone)
            lzones = sorted(lzones, key=lambda d: d['limitUp'], reverse=True)
    
        # Aqui grabamos los zones
        logging.info ("Actualización en estrategia %s", symbol)
        logging.info ("         Nuevas Zonas NOP: %s", lzones)
        globales.G_RTlocalData_.strategies_.strategyPentagramaObj_.strategyPentagramaUpdateZones (symbol, lzones, True)  #Solo actualizo NOP

    # Y actualizamos los graficos
    estrategia = globales.G_RTlocalData_.strategies_.strategyPentagramaObj_.strategyPentagramaGetStrategyBySymbol(symbol)

    if ctx.triggered_id['role'] == 'ZoneInputUp' or ctx.triggered_id['role'] == 'ZoneInputDown':
        fig1 = layout_getFigureHistorico(estrategia)
    else:
        fig1 = no_update

    fig2 = layout_getFigureToday(estrategia, intervalUpdate)

    #return  zonasFilaBorderDown, no_update, no_update
    return  zonasFilaBorderDown, fig1, fig2


# Callback para grabar info de zonas
@appDashFE_.callback(
    Output({'role': 'ZoneInputUp', 'strategySymbol': MATCH, 'index': ALL}, "value"),   # Dash obliga a poner un output. Uno que no se use
    State({'role': 'ZoneInputUp', 'strategySymbol': MATCH, 'index': ALL}, "value"),
    State({'role': 'ZoneInputDown', 'strategySymbol': MATCH, 'index': ALL}, "value"),
    State({'role': 'ZoneInputPos', 'strategySymbol': MATCH, 'index': ALL}, "value"),
    Input({'role': 'ZoneButtonSave', 'strategySymbol': MATCH}, "n_clicks"),
    prevent_initial_call = True,
)
def saveLimites(zoneUps, zoneDowns, zonePos, n_clicks):

    if n_clicks is None or (not ctx.triggered_id):
        raise PreventUpdate

    inputsUps = ctx.states_list[0]
    inputsDowns = ctx.states_list[1]
    inputsPos = ctx.states_list[2]

    ###### Todo esto no hace falta. Solo hace falta copir NOP en normal

    symbol = inputsUps[0]['id']['strategySymbol']  # Lo pillo de esta, pero da igual

    
    #zone = {'reqPos':pos), 'limitUp': float(limit_up), 'limitDown': float(limitdown)}
    #zones = sorted(zones, key=lambda d: d['limitUp'], reverse=True)

    lzones = []
    for i in range (len(inputsUps)):
        zone = {'reqPos':int(inputsPos[i]['value']), 'limitUp': float(inputsUps[i]['value']), 'limitDown': float(inputsDowns[i]['value'])}
        lzones.append(zone)
        lzones = sorted(lzones, key=lambda d: d['limitUp'], reverse=True)

    # Aqui grabamos los zones
    logging.info ("Actualización en estrategia %s", symbol)
    logging.info ("         Nuevas Zonas: %s", lzones)
    globales.G_RTlocalData_.strategies_.strategyPentagramaObj_.strategyPentagramaUpdateZones (symbol, lzones, False)

    return  no_update



# Callback para enable/disable estrategia
@appDashFE_.callback(
    Output({'role': 'switchStratEnabled', 'symbol': MATCH}, "value"),   # Dash obliga a poner un output.
    Input({'role': 'switchStratEnabled', 'symbol': MATCH}, "value"), 
    prevent_initial_call = True,
)
def switchStrategy(state):
    if state:
        logging.info ('Estrategia enabled')
    else:
        logging.info ('Estrategia disabled')

    if not ctx.triggered_id:
        return no_update
    symbol = str(ctx.triggered_id.symbol)
    globales.G_RTlocalData_.strategies_.strategyPentagramaObj_.strategyPentagramaEnableDisable(symbol, state)
    
    return no_update


# Callback para borrar ordenes individualmente
@appDashFE_.callback(
    Output("modalErrorHeader", "children"),
    Output("modalErrorBody", "children"),
    Output("modal_error_main", "is_open"),
    Input({'role': 'boton_order_cancel', 'orderId': ALL}, "n_clicks"),
    Input("modal_boton_close", "n_clicks"),
    State("modal_error_main", "is_open"), prevent_initial_call = True,
)
def cancelOrder (n_button_open, n_button_close, open_status):

    # Esto es por si las moscas
    if not ctx.triggered_id:
        raise PreventUpdate
    
    # Esto es por si las moscas
    pageLoad = True
    for button in  n_button_open:
        if button != None:
            pageLoad = False
    if pageLoad:
        raise PreventUpdate

    responseHeader = ''
    responseBody = ''

    logging.info('Trigger %s', ctx.triggered_id)

    if ctx.triggered_id == "modal_boton_close":
        return responseHeader, responseBody, False

    orderId = ctx.triggered_id['orderId'] 

    #ahora hay que borrarla
    logging.info('CANCEL orderId: %s', str(orderId))
    #return no_update, no_update, no_update

    
    try:
        result = globales.G_RTlocalData_.orderCancelByOrderId (orderId)
        result = True
    except:
        responseHeader = 'Error'
        responseBody = 'Error al cancelar la ordenId: ' + str(orderId)
        
    else:
        if result:
            responseHeader = 'Aceptado'
            responseBody = 'Cancelacion ' + str(orderId) + 'Orden Lanzada'
        else:
            responseHeader = 'Error'
            responseBody = 'Orden no encontrada'

    return responseHeader, responseBody, True


