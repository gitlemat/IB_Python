import globales
from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
from dash import html
from dash import dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from webFE.webFENew_Utils import formatCurrency
import plotly.graph_objects as go
import logging
import random

logger = logging.getLogger(__name__)

def insideDetailsPentagrama (estrategia, graphColumn1, graphColumn2, itemZG):
    # Los detalles de la estrategia (escondidos)
    # Primero las zonas con sus datos

    symbol = estrategia['symbol']
    
    zonasFilaHeader = []
    zonasFilaBorderUp = []
    zonasFilaBorderDown = []
    zonasFilaPosiciones = []
    zonasFilaHeader.append(dbc.Col(''))
    zonasFilaBorderUp.append(dbc.Col('Limit Up', align="center"))
    zonasFilaBorderDown.append(dbc.Col('Limit Down', align="center"))
    zonasFilaPosiciones.append(dbc.Col('Posiciones', align="center"))
    itemZ = 1
    for zone in estrategia['classObject'].zonesNOP_:
        val1 = zone['limitUp']
        val2 = zone['limitDown']
        val3 = zone['reqPos']
        
        zonasFilaHeader.append(dbc.Col('Zona ' + str(itemZ), className="text-center"))
        zonasFilaBorderUp.append(dbc.Col(dbc.Input(id={'role': 'ZoneInputUp', 'strategy':'Pentagrama', 'strategySymbol': symbol, 'index': itemZG}, value=val1, type="text", debounce=True, className="text-end")))
        if itemZ < len(estrategia['classObject'].zonesNOP_):
            zonasFilaBorderDown.append(dbc.Col(dbc.Input(id={'role': 'ZoneInputDown', 'strategy':'Pentagrama', 'strategySymbol': symbol, 'index': itemZG}, value=val2, type="text", debounce=True, readonly= True, className="text-end")))
        else:
            zonasFilaBorderDown.append(dbc.Col(dbc.Input(id={'role': 'ZoneInputDown', 'strategy':'Pentagrama', 'strategySymbol': symbol, 'index': itemZG}, value=val2, type="text", debounce=True, readonly= False, className="text-end")))
        zonasFilaPosiciones.append(dbc.Col(dbc.Input(id={'role': 'ZoneInputPos', 'strategy':'Pentagrama', 'strategySymbol': symbol, 'index': itemZG}, value=val3, type="text", debounce=True, className="text-end")))
        itemZ += 1
        itemZG += 1
    insideDetailsZonas = []
    insideDetailsZonas.append(dbc.Row(zonasFilaHeader))
    insideDetailsZonas.append(dbc.Row(zonasFilaBorderUp))
    insideDetailsZonas.append(dbc.Row(zonasFilaBorderDown, id={'role': 'filaZoneDown', 'strategy':'Pentagrama', 'strategySymbol': symbol}))
    insideDetailsZonas.append(dbc.Row(zonasFilaPosiciones))
    # Ahora los botones de Actualizar/Reset
    insideDetailsBotonesZonas = []
    insideDetailsBotonesZonas.append(dbc.Row(dbc.Button("Actualizar", id={'role': 'ZoneButtonSave', 'strategy':'Pentagrama', 'strategySymbol': symbol}, className="me-2", n_clicks=0)))
    insideDetailsBotonesZonas.append(dbc.Row(dbc.Button("Reset", id={'role': 'ZoneButtonReset', 'strategy':'Pentagrama', 'strategySymbol': symbol}, className="me-2", n_clicks=0)))
    # Y las tablas con ordenes
    insideTable = layout_getStrategyTableOrders(estrategia)
    
    random_wait = random.randint(0,2000) + 3000
    insideOrdenes = html.Div([
        html.Div(
            insideTable, 
            id={'role': 'TableStrategyOrderDetails', 'strategy':'Pentagrama', 'symbol': symbol},
        ),
        dcc.Interval(
            id={'role': 'IntervalOrderTable', 'strategy':'Pentagrama', 'symbol': symbol},
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
        id={'role': 'colapse_strategy', 'strategy':'Pentagrama', 'symbol': symbol},
        is_open=False,
        className = 'mb-3'
    )

    return collapseDetails, itemZG

def layout_getFigureHistoricoPen (estrategia):

    symbol = estrategia['symbol']
    strategyType = estrategia['type']
    contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
    if not contrato:
        logging.error ("Error cargando grafico historico de %s. No tenemos el contrato cargado en RT_Data", symbol)
        return no_update

    fig1 = go.Figure()

    if contrato['dbPandas']:
        df_comp = contrato['dbPandas'].dbGetDataframeComp()
        
        fig1.add_trace(go.Candlestick(x=df_comp.index, open=df_comp['open'], high=df_comp['high'],low=df_comp['low'],close=df_comp['close']))
        fig1 = addZonesLinesHistoricoHE (fig1, estrategia, df_comp)
    
    
    fig1.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
            dict(bounds=[21.1, 15], pattern="hour"),  # hide hours outside of 9.30am-4pm
            #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
        ]
    )

    fig1.update_layout(showlegend=False, 
                       xaxis_rangeslider_visible=False, 
                       title_text='Historico (15min)', 
                       title_x = 0.5,
                       title_xanchor = 'center')

    return fig1

def addZonesLinesHistoricoHE (fig1, estrategia, df_comp):
    limitList= []
    for zone in estrategia['classObject'].zonesNOP_:       
        if zone['limitUp'] not in limitList:
            zoneborder = [zone['limitUp']] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_color="gray", line_width=1, connectgaps = True, fill=None))
            limitList.append(zone['limitUp'])
        if zone['limitDown'] not in limitList:
            zoneborder = [zone['limitDown']] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_color="gray", line_width=1, connectgaps = True, fill=None))
            limitList.append(zone['limitDown'])
            
    return fig1


def layout_getFigureTodayPen (estrategia, update = False):
    symbol = estrategia['symbol']
    strategyType = estrategia['type']
    contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
    if not contrato:
        logging.error ('Error cargando grafico de Hoy de %s. No tenemos el contrato cargado en RT_Data', symbol)
        return no_update
    if (contrato['dbPandas'].toPrint == False) and (update == True):
        logging.debug ('Grafico no actualizado. No hay datos nuevos')
        return no_update
    dfToday = contrato['dbPandas'].dbGetDataframeToday()
    fig2 = go.Figure()

    # Valores de LAST
    fig2.add_trace(go.Scatter(x=dfToday.index, y=dfToday["BID"], mode="lines", line_color="blue", connectgaps = True))
    fig2.add_trace(go.Scatter(x=dfToday.index, y=dfToday["ASK"], mode="lines", line_color="crimson", connectgaps = True))
    
    # Y las zonas
    fig2 = addZonesLinesTodayHE (fig2, estrategia, dfToday)

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


def addZonesLinesTodayHE (fig2, estrategia, dfToday):

    #highlight de la zona actual y precios
    price_Upper = estrategia['classObject'].lastCurrentZoneBufferPriceUp_
    price_Lower = estrategia['classObject'].lastCurrentZoneBufferPriceDown_
    if price_Upper != None and price_Lower != None:
        zoneborder = [price_Upper] * len (dfToday.index)
        fig2.add_trace(go.Scatter(x=dfToday.index, 
                                  y=zoneborder, 
                                  mode="lines", 
                                  line_color="blue", 
                                  line_width=1, 
                                  connectgaps = True, 
                                  fill='none'))
    
        zoneborder = [price_Lower] * len (dfToday.index)
        fig2.add_trace(go.Scatter(x=dfToday.index, 
                                  y=zoneborder, 
                                  mode="lines", 
                                  line_color="blue", 
                                  line_width=1, 
                                  connectgaps = True, 
                                  fillcolor='rgba(0, 0, 255, 0.1)',    #azure = 240, 255, 255
                                  fill='tonexty'))
    # Y las zonas
    limitList= []
    nZone = 0
    for zone in estrategia['classObject'].zonesNOP_:       
        if zone['limitUp'] not in limitList:
            zoneborder = [zone['limitUp']] * len (dfToday.index)
            fig2.add_trace(go.Scatter(x=dfToday.index, 
                                      y=zoneborder, 
                                      mode="lines", 
                                      line_color="gray", 
                                      line_width=1, 
                                      connectgaps = True, 
                                      fill='none'))
            limitList.append(zone['limitUp'])
        if zone['limitDown'] not in limitList:
            zoneborder = [zone['limitDown']] * len (dfToday.index)
            fig2.add_trace(go.Scatter(x=dfToday.index, 
                                      y=zoneborder, 
                                      mode="lines", 
                                      line_color="gray", 
                                      line_width=1, 
                                      connectgaps = True, 
                                      fill='none'))
            limitList.append(zone['limitDown'])
        nZone += 1

    return fig2

def layout_getStrategyTableOrders (estrategia, update = False):

    #orden = globales.G_RTlocalData_.orderGetByOrderId(lOrderId)
    if estrategia['classObject'].ordersUpdated_ == False and update == True:
        logging.debug ('Tabla de ordenes en Strategia no actualizado. No hay datos nuevos')
        return no_update

    ordenUp = globales.G_RTlocalData_.orderGetByOrderId (estrategia['classObject'].UpperOrderId_)
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
        lmtUp = formatCurrency(lmtUp)
        if ordenUp['order'].action == 'SELL':
            posUp = posUp * (-1)
        
    else:
        posUp = 'N/A'
        lmtUp = 'N/A'
        typeUp = 'N/A'
        statusUp = 'N/A'
    
    ordenDown = globales.G_RTlocalData_.orderGetByOrderId (estrategia['classObject'].LowerOrderId_)
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
        lmtDown = formatCurrency(lmtDown)
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
            html.Td(str(estrategia['classObject'].UpperOrderId_)),
            html.Td(str(estrategia['classObject'].UpperOrderPermId_)),
            html.Td(str(lmtUp)),
            html.Td(str(typeUp)),
            html.Td(str(statusUp)),
            html.Td(str(posUp)),
        ]
    )

    insideDetailsTableRowDwn = html.Tr(
        [
            html.Td("Orden Down"), 
            html.Td(str(estrategia['classObject'].LowerOrderId_)),
            html.Td(str(estrategia['classObject'].LowerOrderPermId_)),
            html.Td(str(lmtDown)),
            html.Td(str(typeDown)),
            html.Td(str(statusDown)),
            html.Td(str(posDown)),
        ]
    )

    insideDetailsTableBody = [html.Tbody([insideDetailsTableRowUp, insideDetailsTableRowDwn])]
    estrategia['classObject'].ordersUpdated_ = False

    ret = dbc.Table(
        insideDetailsTableHeader + insideDetailsTableBody, 
        bordered=True
    )

    return ret

#Callback para actualizar tabla de ordenes en Strategy
@callback(
    Output({'role':'TableStrategyOrderDetails', 'strategy':'Pentagrama', 'symbol': MATCH}, "children"),
    Input({'role': 'IntervalOrderTable', 'strategy':'Pentagrama', 'symbol': MATCH}, 'n_intervals'),
    prevent_initial_call = True,
)
def actualizarTablaOrdenesStrategiesPen (n_intervals):
    if not ctx.triggered_id:
        raise PreventUpdate
    logging.debug ('Actualizando tabla ordenes estrategia')
    symbol = ctx.triggered_id['symbol']

    estrategia = globales.G_RTlocalData_.strategies_.strategyGetStrategyBySymbolAndType (symbol, 'Pentagrama')
    resp = layout_getStrategyTableOrders (estrategia, True)

    return resp

# Callback para sincronizar limites de zona, definir limites
# Y actualizar graphs
@callback(
    Output({'role': 'filaZoneDown', 'strategy':'Pentagrama', 'strategySymbol': MATCH}, "children"),
    Output({'role': 'graphDetailsComp', 'strategy':'Pentagrama', 'strategySymbol': MATCH}, 'figure'),
    Output({'role': 'graphDetailsToday', 'strategy':'Pentagrama', 'strategySymbol': MATCH}, 'figure'),
    Input({'role': 'ZoneInputUp', 'strategy':'Pentagrama', 'strategySymbol': MATCH, 'index': ALL}, "value"),
    Input({'role': 'ZoneInputDown', 'strategy':'Pentagrama', 'strategySymbol': MATCH, 'index': ALL}, "value"),
    Input({'role': 'ZoneInputPos', 'strategy':'Pentagrama', 'strategySymbol': MATCH, 'index': ALL}, "value"),
    Input({'role': 'IntervalgraphToday', 'strategy':'Pentagrama', 'strategySymbol': MATCH}, 'n_intervals'),
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
        globales.G_RTlocalData_.strategies_.strategyUpdateZones (symbol, 'Pentagrama', lzones, True)  #Solo actualizo NOP

    # Y actualizamos los graficos
    estrategia = globales.G_RTlocalData_.strategies_.strategyGetStrategyBySymbolAndType (symbol, 'Pentagrama')

    if ctx.triggered_id['role'] == 'ZoneInputUp' or ctx.triggered_id['role'] == 'ZoneInputDown':
        fig1 = layout_getFigureHistoricoPen(estrategia)
    else:
        fig1 = no_update

    fig2 = layout_getFigureTodayPen(estrategia, intervalUpdate)

    #return  zonasFilaBorderDown, no_update, no_update
    return  zonasFilaBorderDown, fig1, fig2


# Callback para grabar info de zonas
@callback(
    Output({'role': 'ZoneInputUp', 'strategy':'Pentagrama', 'strategySymbol': MATCH, 'index': ALL}, "value"),   # Dash obliga a poner un output. Uno que no se use
    State({'role': 'ZoneInputUp', 'strategy':'Pentagrama', 'strategySymbol': MATCH, 'index': ALL}, "value"),
    State({'role': 'ZoneInputDown', 'strategy':'Pentagrama', 'strategySymbol': MATCH, 'index': ALL}, "value"),
    State({'role': 'ZoneInputPos', 'strategy':'Pentagrama', 'strategySymbol': MATCH, 'index': ALL}, "value"),
    Input({'role': 'ZoneButtonSave', 'strategy':'Pentagrama', 'strategySymbol': MATCH}, "n_clicks"),
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
    globales.G_RTlocalData_.strategies_.strategyUpdateZones (symbol, 'Pentagrama', lzones, False)

    return  no_update
