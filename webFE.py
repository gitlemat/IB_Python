from flask import Flask
from dash import Dash, html, dcc, MATCH, ALL, Input, Output, State, ctx, no_update, dash
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import globales
import logging
import random
import pandas as pd


logger = logging.getLogger(__name__)


appDashFE_ = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
appDashFE_.title = "IB RODSIC"

#####################################################################################################################
#####################################################################################################################
## Ordenes

def layout_ordenes_tab ():
    data = globales.G_RTlocalData_.orderReturnListAll()
    ContentItems = []
    item = 0
    #################################
    # Preparacion de Tab de contratos
    for orden in data:
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
                    dbc.Col(dbc.Button(str(lOrderId),id={'role': 'boton', 'index': item}), className = 'bg-primary mr-1', width = 1),
                    dbc.Col(html.Div(symbol), className = 'bg-primary mr-1', width = 3),
                    dbc.Col(html.Div(lAction), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div(lStatus), className = 'bg-success', width = 1),
                    dbc.Col(html.Div(lFillState), className = 'bg-primary', width = 2),
                    dbc.Col(html.Div(lLastFillPrice), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("Comment"), className = 'bg-primary', width = 3),
                ], className = 'text-white mb-1',
        )  

        lorderType = orden['order'].orderType
        lPermId = str(orden['order'].permId)
        lgConId = str(orden['contractId'])
        lLmtPrice = str(orden['order'].lmtPrice)
        lTif = orden['order'].tif

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
            id={'role': 'colapse', 'index': item},
            is_open=False,
        )


        ContentItems.append({"header": headerRow, "details": collapseDetails})
        item += 1

    #################################
    # Ahora creamos el tab de ordenes usando la info anterior
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
                    dbc.Col(html.Div("Comment"), className = 'bg-primary', width = 3),
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
            posQty = "0"
            posavgCost = "0"
        else:
            posQty = str(posicion) 
            posavgCost = str(contrato['posAvgPrice'])
        priceBuy = str(contrato['currentPrices']['BUY'])
        priceSell = str(contrato['currentPrices']['SELL'])
        priceLast = str(contrato['currentPrices']['LAST'])
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
        posQty = estrategia['currentPos']
        stratEnabled = estrategia['stratEnabled']
        contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
        # Cabecera para cada contrato con estrategia
        headerRow = dbc.Row(
                [
                    dbc.Col(dbc.Button(symbol,id={'role': 'boton', 'index': item}), className = 'bg-primary mr-1', width = 4),
                    dbc.Col(html.Div(posQty), className = 'bg-primary mr-1', width = 1),
                    dbc.Col(html.Div(""), className = 'bg-primary mr-1', width = 6),
                    dbc.Col(dbc.Switch(id={'role': 'switchStratEnabled', 'symbol': symbol}, value = stratEnabled), className = 'bg-primary mr-1', width = 1),
                ], className = 'text-white mb-1',
        )

        # Los dos graficos
        fig1 = layout_getFigureHistorico(estrategia)   # Lo tengo en una funcion para que sea facil actualizar
        graphColumn1 = html.Div(
            dcc.Graph(
                    id={'role': 'graphDetailsComp', 'gConId': str(contrato['gConId'])},
                    animate = False,
                    figure = fig1
            )
        )
        
        random_wait = random.randint(0,1000) + 10000
        fig2 = layout_getFigureToday(estrategia)   # Lo tengo en una funcion para que sea facil actualizar
        graphColumn2 = html.Div([
            dcc.Graph(
                    id={'role': 'graphDetailsToday', 'gConId': str(contrato['gConId'])},
                    animate = False,
                    figure = fig2
            ),
            dcc.Interval(
                id={'role': 'IntervalgraphToday', 'gConId': str(contrato['gConId'])},
                interval= random_wait, # in milliseconds
                n_intervals=0
            )
        ])
        
        # Los detalles de la estrategia (escondidos)
        
        insideDetailsOrdenes = []
        insideDetailsOrdenes.append(html.Div(children = "Posiciones de la Estrategia: " + str(estrategia['currentPos'])))
        insideDetailsOrdenes.append(html.Div(children = "Orden Superior Actual (OrderId/PermId): " + str(estrategia['UpperOrderId']) + '/' + str(estrategia['UpperOrderPermId'])))
        insideDetailsOrdenes.append(html.Div(children = "Orden Inferior Actual (OrderId/PermId): " + str(estrategia['LowerOrderId']) + '/' + str(estrategia['LowerOrderPermId'])))

        zonasFilaHeader = []
        zonasFilaBorderUp = []
        zonasFilaBorderDown = []
        zonasFilaPosiciones = []
        zonasFilaHeader.append(dbc.Col(''))
        zonasFilaBorderUp.append(dbc.Col('Limit Up', align="center"))
        zonasFilaBorderDown.append(dbc.Col('Limit Down', align="center"))
        zonasFilaPosiciones.append(dbc.Col('Posiciones', align="center"))
        itemZ = 1
        for zone in estrategia['zones']:
            val1 = zone['limitUp']
            val2 = zone['limitDown']
            val3 = zone['reqPos']
            
            zonasFilaHeader.append(dbc.Col('Zona ' + str(itemZ), className="text-center"))
            zonasFilaBorderUp.append(dbc.Col(dbc.Input(id={'role': 'ZoneInputUp', 'strategySymbol': symbol, 'index': itemZG}, value=val1, type="text", className="text-end")))
            if itemZ < len(estrategia['zones']):
                zonasFilaBorderDown.append(dbc.Col(dbc.Input(id={'role': 'ZoneInputDown', 'strategySymbol': symbol, 'index': itemZG}, value=val2, type="text", readonly= True, className="text-end")))
            else:
                zonasFilaBorderDown.append(dbc.Col(dbc.Input(id={'role': 'ZoneInputDown', 'strategySymbol': symbol, 'index': itemZG}, value=val2, type="text", readonly= False, className="text-end")))
            zonasFilaPosiciones.append(dbc.Col(dbc.Input(id={'role': 'ZoneInputPos', 'strategySymbol': symbol, 'index': itemZG}, value=val3, type="text", className="text-end")))
            itemZ += 1
            itemZG += 1

        insideDetailsZonas = []
        insideDetailsZonas.append(dbc.Row(zonasFilaHeader))
        insideDetailsZonas.append(dbc.Row(zonasFilaBorderUp))
        insideDetailsZonas.append(dbc.Row(zonasFilaBorderDown, id={'role': 'filaZoneDown', 'strategySymbol': symbol}))
        insideDetailsZonas.append(dbc.Row(zonasFilaPosiciones))

        insideDetailsBotonesZonas = []
        insideDetailsBotonesZonas.append(dbc.Button("Actualizar", id={'role': 'ZoneButtonSave', 'strategySymbol': symbol}, className="me-2", n_clicks=0))
        insideDetailsBotonesZonas.append(dbc.Button("Reset", id={'role': 'ZoneButtonReset', 'strategySymbol': symbol}, className="me-2", n_clicks=0))

        insideDetails = []
        insideDetails.append(dbc.Col(insideDetailsZonas, width=6))
        insideDetails.append(dbc.Col(insideDetailsBotonesZonas, width=1))
        insideDetails.append(dbc.Col(insideDetailsOrdenes, width=5))
        # Todo lo que se oculta junto
        collapseDetails = dbc.Collapse(
            [
                dbc.Row(
                    [
                        dbc.Col(graphColumn1, width=6),
                        dbc.Col(graphColumn2, width=6)
                    ]
                ),
                dbc.Row(
                        insideDetails,
                )
            ],
            id={'role': 'colapse', 'index': item},
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
                    dbc.Col(html.Div("Comment"), className = 'bg-primary', width = 6),
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

    df_comp = contrato['dbPandas'].dbGetDataframeComp()
    fig1 = go.Figure()
    fig1.add_trace(go.Candlestick(x=df_comp.index, open=df_comp['open'], high=df_comp['high'],low=df_comp['low'],close=df_comp['close']))
    limitList= []
    for zone in estrategia['zones']:       
        if zone['limitUp'] not in limitList:
            zoneborder = [zone['limitUp']] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_color="gray", line_width=1, connectgaps = True, fill=None))
            limitList.append(zone['limitUp'])
        if zone['limitDown'] not in limitList:
            zoneborder = [zone['limitDown']] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_color="gray", line_width=1, connectgaps = True, fill=None))
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



def layout_getFigureToday (estrategia):
    symbol = estrategia['symbol']
    contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
    if contrato['dbPandas'].toPrint == False:
        logging.info ('Grafico no actualizado ')
        return no_update
    dfToday = contrato['dbPandas'].dbGetDataframeToday()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=dfToday['timestamp'], y=dfToday["LAST"], mode="lines", line_color="crimson", connectgaps = True))
    limitList= []
    for zone in estrategia['zones']:       
        if zone['limitUp'] not in limitList:
            zoneborder = [zone['limitUp']] * len (dfToday.index)
            fig2.add_trace(go.Scatter(x=dfToday["timestamp"], 
                                      y=zoneborder, 
                                      mode="lines", 
                                      line_color="gray", 
                                      line_width=1, 
                                      connectgaps = True, 
                                      fill=None))
            limitList.append(zone['limitUp'])
        if zone['limitDown'] not in limitList:
            zoneborder = [zone['limitDown']] * len (dfToday.index)
            fig2.add_trace(go.Scatter(x=dfToday["timestamp"], 
                                      y=zoneborder, 
                                      mode="lines", 
                                      line_color="gray", 
                                      line_width=1, 
                                      connectgaps = True, 
                                      fill=None))
    fig2.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
            dict(bounds=[20.25, 15.66], pattern="hour"),  # hide hours outside of 9.30am-4pm
            #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
        ]
    )

    rannn = str(random.randint(0,1000))
    logging.info ('Grafico actualizado con %s', rannn)
    fig2.update_layout(showlegend=False, 
                       title_text='Datos Tiempo Real Hoy'+rannn, 
                       title_x = 0.5,
                       title_xanchor = 'center')

    contrato['dbPandas'].toPrint = False

    return fig2


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

    layout = dbc.Container(tabs)

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

# Callback para colapsar o mostrar filas
@appDashFE_.callback(
    Output({'role': 'colapse', 'index': MATCH}, "is_open"),
    Input({'role': 'boton', 'index': MATCH}, "n_clicks"),
    State({'role': 'colapse', 'index': MATCH}, "is_open"),
)
def toggle_left(n_button, is_open):
    if n_button:
        return not is_open
    return is_open

# Callback para sincronizar limites de zona
@appDashFE_.callback(
    Output({'role': 'filaZoneDown', 'strategySymbol': MATCH}, "children"), 
    Input({'role': 'ZoneInputUp', 'strategySymbol': MATCH, 'index': ALL}, "value"),
    Input({'role': 'ZoneInputDown', 'strategySymbol': MATCH, 'index': ALL}, "value"),
)
def syncLimites(zoneUps, zoneDowns):
    inputsUps = ctx.inputs_list[0]
    inputsDowns = ctx.inputs_list[1]

    if not ctx.triggered_id:
        return no_update

    zonasFilaBorderDown = []
    zonasFilaBorderDown.append(dbc.Col('Limit Down', align="center"))
    for i in range(len(inputsDowns) -1):
        zoneD = inputsDowns[i]
        val = inputsUps[i+1]['value']
        zonasFilaBorderDown.append(dbc.Col(dbc.Input(id=zoneD['id'], value=val, type="text", readonly= True, className="text-end")))
    zoneD = inputsDowns[-1]
    val = inputsDowns[-1]['value']
    zonasFilaBorderDown.append(dbc.Col(dbc.Input(id=zoneD['id'], value=val, type="text", readonly= False, className="text-end")))
    return  zonasFilaBorderDown

'''
# Callback para grabar info de zonas
@appDashFE_.callback(
    Output({'role': 'ZoneInputUp', 'strategySymbol': MATCH, 'index': ALL}, "value"),   # Dash obliga a poner un output.
    Input({'role': 'ZoneInputUp', 'strategySymbol': MATCH, 'index': ALL}, "value"),
    Input({'role': 'ZoneInputDown', 'strategySymbol': MATCH, 'index': ALL}, "value"),
    Input({'role': 'ZoneInputPos', 'strategySymbol': MATCH, 'index': ALL}, "value"),
)
def saveLimites(zoneUps, zoneDowns, zonePos):
    inputsUps = ctx.inputs_list[0]
    inputsDowns = ctx.inputs_list[1]
    inputsPos = ctx.inputs_list[2]

    symbol = inputsUps['id']['strategySymbol']  # Lo pillo de esta, pero da igual

    if not ctx.triggered_id:
        return no_update
    #zone = {'reqPos':pos), 'limitUp': float(limit_up), 'limitDown': float(limitdown)}
    #zones = sorted(zones, key=lambda d: d['limitUp'], reverse=True)

    zones = []
    for i in range (len(inputsUps)):
        zone = {'reqPos':inputsPos[i], 'limitUp': inputsUps[i], 'limitDown': inputsDowns[i]}
        zones.append(zone)
        zones = sorted(zones, key=lambda d: d['limitUp'], reverse=True)

    # Aqui grabamos los zones
    globales.G_RTlocalData_.strategies_.strategyPentagramaObj_strategyPentagramaUpdateZones (symbol, zones)

    return  no_update

'''

# Callback para enable/disable estrategia
@appDashFE_.callback(
    Output({'role': 'switchStratEnabled', 'symbol': MATCH}, "value"),   # Dash obliga a poner un output.
    Input({'role': 'switchStratEnabled', 'symbol': MATCH}, "value"),
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

# Callbacl para actualizar graphs de today
@appDashFE_.callback(
    Output({'role': 'graphDetailsToday', 'gConId': MATCH}, 'figure'),
    Input({'role': 'IntervalgraphToday', 'gConId': MATCH}, 'n_intervals')
)
def update_graph_live(n_int):
    if not ctx.triggered_id:
        return no_update
    gConId = str(ctx.triggered_id.gConId)
    strategyMariposaVerano_ = globales.G_RTlocalData_.strategies_.strategyPentagramaObj_.strategyPentagramaGetAll()
    for estrategia in strategyMariposaVerano_:
        symbol = estrategia['symbol']
        contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
        if not contrato:
            logging.info ("No contrato")
            continue
        if str(contrato['gConId']) == gConId:
            logging.info ("Son iguales")
            fig2 = layout_getFigureToday(estrategia)
            return fig2

    logging.info ("No he encontrado la figura")
    return no_update


