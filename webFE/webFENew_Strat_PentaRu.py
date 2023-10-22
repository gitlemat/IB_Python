from webFE.webFENew_Utils import formatCurrency
from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
from dash import html
from dash import dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dash_table
from dash.dash_table.Format import Format, Group, Prefix, Scheme, Symbol
import globales
import logging
import random

logger = logging.getLogger(__name__)

def insideDetailsPentagramaRu (estrategia, graphColumn1, graphColumn2, graphComponentes):
    # Y las tablas con ordenes

    symbol = estrategia['symbol']

    # Hacemos los botones e info inicial

    # Cerrar posiciones

    cerrarPos = estrategia['classObject'].cerrarPos_

    grupo_switches = html.Div(
        [
            dbc.Switch(
                    id={'role': 'switch_cerrarPos', 'strategy':'PentagramaRu', 'symbol': symbol},
                    label="Dejar cerrar las posiciones y no regenerar",
                    value=cerrarPos,
                )
        ]
    )

    # El boton de recarga

    boton_reload = dbc.Button("Recargar desde Fichero", id={'role': 'ZoneButtonReload', 'strategy':'PentagramaRu', 'symbol': symbol}, className="me-2", n_clicks=0)

    # Contenigo de caja
    
    contenido_caja = html.Div(
        dbc.Row(
                [
                    dbc.Col(grupo_switches, width=10),
                    dbc.Col(boton_reload, width=2)
                ]
            ),
        )

    caja_inicial_top = dbc.Card(contenido_caja, body=True),
 

    # Hacemos la tabla de ordenes

    insideTable = layout_getStrategyPenRuTableOrders(estrategia)
    
    random_wait = random.randint(0,2000) + 3000
    insideOrdenes = html.Div([
        html.Div(
            insideTable, 
            id={'role': 'TableStrategyOrderDetails', 'strategy':'PentagramaRu', 'symbol': symbol},
        ),
        dcc.Interval(
            id={'role': 'IntervalOrderTable', 'strategy':'PentagramaRu', 'symbol': symbol},
            interval= random_wait, # in milliseconds
            n_intervals=0
        )
    ])

    # Las ordenes ejecutadas de PentagramaRu

    df_execs = estrategia['classObject'].pandas_.dbGetExecsDataframeAll()
    df_execs.sort_index(ascending=False, inplace = True)
    df_execs['timestamp'] = df_execs.index.strftime("%d/%m/%Y - %H:%M:%S")

    columnas = [
        {'id': "timestamp", 'name': "Fecha", 'type': 'datetime'},
        {'id': "OrderId", 'name': "OrderId", 'type': 'numeric'},
        {'id': "Side", 'name': "Side", 'type': 'text'},
        {'id': "FillPrice", 'name': "Precio", 'type': 'numeric', 'format': Format(symbol=Symbol.yes, symbol_prefix='$', precision=3)},
        {'id': "Quantity", 'name': "Qty", 'type': 'numeric'},
        {'id': "RealizedPnL", 'name': "PnL", 'type': 'numeric', 'format': Format(symbol=Symbol.yes, symbol_prefix='$', precision=3)},
        {'id': "Commission", 'name': "Comisión", 'type': 'numeric', 'format': Format(symbol=Symbol.yes, symbol_prefix='$', precision=3)},
    ]

    tablaExecs = dash_table.DataTable (
        data = df_execs.to_dict('records'), 
        columns = columnas,
        page_size=10
    )
    
    # Todo lo que se oculta junto
    collapseDetails = dbc.Collapse(
        [
            dbc.Row(
                    caja_inicial_top, className = 'mb-3' 
            ),
            dbc.Row(
                [
                    dbc.Col(graphColumn1, width=6),
                    dbc.Col(graphColumn2, width=6)
                ],  className = 'mb-3' 
            ),
            dbc.Row(
                    tablaExecs,
            ),
            dbc.Row(
                    graphComponentes, className = 'mb-3' 
            ),
            dbc.Row(
                    insideOrdenes,
            ), 
            modal_ordenFix()
        ],
        id={'role': 'colapse_strategy', 'strategy':'PentagramaRu', 'symbol': symbol},
        is_open=False,
        className = 'mb-3'
    )

    return collapseDetails

def layout_getFigureHistoricoPenRu (estrategia):

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
        fig1 = addZonesLinesHistoricoRu (fig1, estrategia, df_comp)

    
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
                       title_xanchor = 'center',
                       margin=dict(l=10, r=10, t=40, b=40))

    return fig1


def addZonesLinesHistoricoRu (fig1, estrategia, df_comp):
    limitList= []
    for zone in estrategia['classObject'].zones_: 

        ordenMain = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderId_)
        ordenSL = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderIdSL_)
        ordenTP = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderIdTP_)

        if zone['orderBlock'].Price_ not in limitList:
            zoneborder = [zone['orderBlock'].Price_] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_color="gray", line_width=1, connectgaps = True, fill=None))
            limitList.append(zone['orderBlock'].Price_)
        if zone['orderBlock'].PrecioSL_ not in limitList:
            zoneborder = [zone['orderBlock'].PrecioSL_] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_dash='dash', line_color="gray", line_width=1, connectgaps = True, fill=None))
            limitList.append(zone['orderBlock'].PrecioSL_)
        if zone['orderBlock'].PrecioTP_ not in limitList:
            zoneborder = [zone['orderBlock'].PrecioTP_] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_dash='dash', line_color="gray", line_width=1, connectgaps = True, fill=None))
            limitList.append(zone['orderBlock'].PrecioTP_)


    return fig1

def layout_getFigureTodayPenRu (estrategia, update = False):
    if estrategia == None:
        return no_update
    symbol = estrategia['symbol']
    strategyType = estrategia['type']
    contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
    if not contrato:
        logging.error ('Error cargando grafico de Hoy de %s. No tenemos el contrato cargado en RT_Data', symbol)
        return no_update
    if contrato['dbPandas'] == None:
        return no_update
    if (contrato['dbPandas'].toPrint == False) and (update == True):
        logging.debug ('Grafico no actualizado. No hay datos nuevos')
        return no_update
    dfToday = contrato['dbPandas'].dbGetDataframeToday()
    fig2 = go.Figure()

    # Valores de LAST
    fig2.add_trace(go.Candlestick(x=dfToday.index, open=dfToday['open'], high=dfToday['high'],low=dfToday['low'],close=dfToday['close']))
    #fig2.add_trace(go.Scatter(x=dfToday.index, y=dfToday["BID"], mode="lines", line_color="blue", connectgaps = True))
    #fig2.add_trace(go.Scatter(x=dfToday.index, y=dfToday["ASK"], mode="lines", line_color="green", connectgaps = True))
    #fig2.add_trace(go.Scatter(x=dfToday.index, y=dfToday["LAST"], mode="lines", line_color="crimson", connectgaps = True))
    
    # Y las zonas
    fig2 = addZonesLinesTodayRu (fig2, estrategia, dfToday)

    fig2.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
            dict(bounds=[20.25, 15.16], pattern="hour"),  # hide hours outside of 9.30am-4pm
            #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
        ]
    )

    rannn = str(random.randint(0,1000))
    logging.debug ('Grafico actualizado con %s', rannn)
    fig2.update_layout(showlegend=False, 
                       xaxis_rangeslider_visible=False, 
                       title_text='Datos Tiempo Real Hoy', 
                       title_x = 0.5,
                       title_xanchor = 'center',
                       margin=dict(l=10, r=10, t=40, b=40))

    contrato['dbPandas'].toPrint = False

    return fig2

def addZonesLinesTodayRu (fig2, estrategia, dfToday):
    limitList= []
    for zone in estrategia['classObject'].zones_:  
        ordenMain = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderId_)
        ordenSL = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderIdSL_)
        ordenTP = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderIdTP_)

        if zone['orderBlock'].Price_ not in limitList:
            if ordenMain != None and ordenMain['params'] != None and 'status' in ordenMain['params']:
                if ordenMain['params']['status'] == 'Submitted':
                    zoneborder = [zone['orderBlock'].Price_] * len (dfToday.index)
                    fig2.add_trace(go.Scatter(x=dfToday.index, y=zoneborder, mode="lines", line_color="gray", line_width=1, connectgaps = True, fill=None))
                    limitList.append(zone['orderBlock'].Price_)
        if zone['orderBlock'].PrecioSL_ not in limitList:
            if ordenSL != None and ordenSL['params'] != None and 'status' in ordenSL['params']:
                if ordenSL['params']['status'] == 'Submitted':
                    zoneborder = [zone['orderBlock'].PrecioSL_] * len (dfToday.index)
                    fig2.add_trace(go.Scatter(x=dfToday.index, y=zoneborder, mode="lines", line_dash='dash', line_color="gray", line_width=1, connectgaps = True, fill=None))
                    limitList.append(zone['orderBlock'].PrecioSL_)
        if zone['orderBlock'].PrecioTP_ not in limitList:
            if ordenTP != None and ordenTP['params'] != None and 'status' in ordenTP['params']:
                if ordenTP['params']['status'] == 'Submitted':
                    zoneborder = [zone['orderBlock'].PrecioTP_] * len (dfToday.index)
                    fig2.add_trace(go.Scatter(x=dfToday.index, y=zoneborder, mode="lines", line_dash='dash', line_color="gray", line_width=1, connectgaps = True, fill=None))
                    limitList.append(zone['orderBlock'].PrecioTP_)

    return fig2



def layout_getStrategyPenRuTableOrders (estrategia, update = False):

    #orden = globales.G_RTlocalData_.orderGetByOrderId(lOrderId)
    if estrategia['classObject'].ordersUpdated_ == False and update == True:
        logging.debug ('Tabla de ordenes en Strategia no actualizado. No hay datos nuevos')
        return no_update

    symbol = estrategia['classObject'].symbol_

    insideDetailsTableHeader = [
        html.Thead(
            html.Tr(
                [
                   html.Th(""), 
                   html.Th("Order Id"),
                   html.Th("Perm Id"),
                   html.Th("Lmt"),
                   html.Th("Type"),
                   html.Th("Action"),
                   html.Th("Status"),
                   html.Th("Qty"),
                   html.Th("Fix"),
                ], style={'color':'#ffffff','background-color':'#636363'}
            )   
        )
    ]

    insideDetailsTableBodyInside = []

    for zone in estrategia['classObject'].zones_:
        #ordenParent = globales.G_RTlocalData_.orderGetByOrderId (zone['OrderId'])
        ordenParent = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderId_)
        fixOCA = False
        fixParent = False
        if zone['orderBlock'].toFix == 1:
            fixParent = True
            # Parent Rota y fix necesario
        if zone['orderBlock'].toFix == 2:
            fixOCA = True
            # OCA Rota y fix necesario
        if zone['orderBlock'].toFix == 3:
            fixParent = True
            fixOCA = True
        if ordenParent:
            posParent = ordenParent['order'].totalQuantity
            typeParent = ordenParent['order'].orderType
            if ordenParent['params'] != None and 'status' in ordenParent['params']:
                statusParent = ordenParent['params']['status']
            else:
                statusParent = 'N/A'
            lmtParent = ordenParent['order'].lmtPrice
            actionParent = ordenParent['order'].action
            if ordenParent['order'].orderType == 'STP':  # No va a pasar nunca
                lmtParent = ordenParent['order'].auxPrice
        else:
            posParent = zone['orderBlock'].Qty_
            lmtParent = zone['orderBlock'].Price_
            if zone['orderBlock'].B_S_ == 'S':
                actionParent = 'SELL'
            else:
                actionParent = 'BUY'
            typeParent = 'LMT'
            statusParent = 'N/A'

        if actionParent == 'SELL':
            posParent = posParent * (-1)
        lmtParent = formatCurrency(lmtParent)

        #ordenTP = globales.G_RTlocalData_.orderGetByOrderId (zone['OrderIdTP'])
        ordenTP = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderIdTP_)
        if ordenTP:
            posTP = ordenTP['order'].totalQuantity
            typeTP = ordenTP['order'].orderType
            if ordenTP['params'] != None and 'status' in ordenTP['params']:
                statusTP = ordenTP['params']['status']
            else:
                statusTP = 'N/A'
            lmtTP = ordenTP['order'].lmtPrice
            actionTP = ordenTP['order'].action
            if ordenTP['order'].orderType == 'STP':
                lmtTP = ordenTP['order'].auxPrice
        else:
            posTP = zone['orderBlock'].Qty_
            lmtTP = zone['orderBlock'].PrecioTP_
            actionTP = "SELL" if actionParent == "BUY" else "BUY"
            typeTP = 'LMT'
            statusTP = 'N/A'

        if actionTP == 'SELL':
            posTP = posTP * (-1)
        lmtTP = formatCurrency(lmtTP)

        #ordenSL = globales.G_RTlocalData_.orderGetByOrderId (zone['OrderIdSL'])
        ordenSL = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderIdSL_)
        if ordenSL:
            posSL = ordenSL['order'].totalQuantity
            typeSL = ordenSL['order'].orderType
            if ordenSL['params'] != None and 'status' in ordenSL['params']:
                statusSL = ordenSL['params']['status']
            else:
                statusSL = 'N/A'
            lmtSL = ordenSL['order'].lmtPrice
            actionSL = ordenSL['order'].action
            if ordenSL['order'].orderType == 'STP':
                lmtSL = ordenSL['order'].auxPrice
            if ordenSL['order'].action == 'SELL':
                posSL = posSL * (-1)
        else:
            posSL = zone['orderBlock'].Qty_
            lmtSL = zone['orderBlock'].PrecioSL_
            actionSL = "SELL" if actionParent == "BUY" else "BUY"
            typeSL = 'STP'
            statusSL = 'N/A'

        if actionSL == 'SELL':
            posSL = posSL * (-1)
        lmtSL = formatCurrency(lmtSL)

        backgroundColorParent = '#c1c2c9'
        backgroundColorTP = '#e4e5ed'
        backgroundColorSL = '#e4e5ed'
        if statusParent in ['Filled']:
            backgroundColorParent = '#caf5c9' # Todo bien
        if statusParent in ['N/A']:
            if zone['orderBlock'].BracketOrderFilledState_ in ['ParentFilled', 'ParentFilled+F']:
                backgroundColorParent = '#caf5c9' # Bien
            else:
                backgroundColorParent = '#d6bfba' # Mal

        if statusTP in ['Filled']:
            backgroundColorTP = '#caf5c9'
        if statusTP in ['N/A']:
            backgroundColorTP = '#cf5338'
        if statusSL in ['Filled']:
            backgroundColorSL = '#cf5338'
        if statusSL in ['N/A']:
            backgroundColorSL = '#cf5338'

        disableOcaFix = not fixOCA
        disableParentFix = not fixParent

        insideDetailsStratParent = html.Tr(
            [
                html.Td("Parent"), 
                #html.Td(str(zone['OrderId'])),
                #html.Td(str(zone['OrderPermId'])),
                html.Td(str(zone['orderBlock'].orderId_)),
                html.Td(str(zone['orderBlock'].orderPermId_)),
                html.Td(str(lmtParent)),
                html.Td(str(typeParent)),
                html.Td(str(actionParent)),
                html.Td(str(statusParent)),
                html.Td(str(posParent)),
                html.Td(dbc.Button(html.I(className="bi bi-bandaid me-2"),id={'role': 'boton_fix', 'orderId': zone['orderBlock'].orderId_, 'symbol': symbol}, style={'color': '#000000', 'background-color': 'transparent', 'border-color': 'transparent'}, disabled=disableParentFix)),
            ], style={'color':'#000000','background-color':backgroundColorParent}
        )

        insideDetailsStratTP = html.Tr(
            [
                html.Td("T Profit", style={"textAlign": "right"}), 
                #html.Td(str(zone['OrderIdTP'])),
                #html.Td(str(zone['OrderPermIdTP'])),
                html.Td(str(zone['orderBlock'].orderIdTP_)),
                html.Td(str(zone['orderBlock'].orderPermIdTP_)),
                html.Td(str(lmtTP)),
                html.Td(str(typeTP)),
                html.Td(str(actionTP)),
                html.Td(str(statusTP)),
                html.Td(str(posTP)),
                html.Td(dbc.Button(html.I(className="bi bi-bandaid me-2"),id={'role': 'boton_fix', 'orderId': zone['orderBlock'].orderIdTP_, 'symbol': symbol}, style={'color': '#000000', 'background-color': 'transparent', 'border-color': 'transparent'}, disabled=disableOcaFix)),
            ], style={'color':'#000000','background-color':backgroundColorTP}
        )

        insideDetailsStratSL = html.Tr(
            [
                html.Td("Stop Loss", style={"textAlign": "right"}), 
                #html.Td(str(zone['OrderIdSL'])),
                #html.Td(str(zone['OrderPermIdSL'])),
                html.Td(str(zone['orderBlock'].orderIdSL_)),
                html.Td(str(zone['orderBlock'].orderPermIdSL_)),
                html.Td(str(lmtSL)),
                html.Td(str(typeSL)),
                html.Td(str(actionSL)),
                html.Td(str(statusSL)),
                html.Td(str(posSL)),
                html.Td(dbc.Button(html.I(className="bi bi-bandaid me-2"),id={'role': 'boton_fix', 'orderId': zone['orderBlock'].orderIdSL_, 'symbol': symbol}, style={'color': '#000000', 'background-color': 'transparent', 'border-color': 'transparent'}, disabled=disableOcaFix)),
            ], style={'color':'#000000','background-color':backgroundColorSL}
        )

        insideDetailsStratEmpty = html.Tr("", style={'height':'10px'})

        insideDetailsTableBodyInside.append(insideDetailsStratParent)
        insideDetailsTableBodyInside.append(insideDetailsStratTP)
        insideDetailsTableBodyInside.append(insideDetailsStratSL)
        insideDetailsTableBodyInside.append(insideDetailsStratEmpty)


    insideDetailsTableBody = [html.Tbody(insideDetailsTableBodyInside)]
    estrategia['classObject'].ordersUpdated_ = False

    ret = dbc.Table(
        insideDetailsTableHeader + insideDetailsTableBody, 
        bordered=True
    )

    return ret

def modal_ordenFix():

    orderOrderId = dcc.Input(
        id = "order_fix_orderId",
        type = "text",
        readOnly = True,
        placeholder = "",
    )

    orderStratType = dcc.Input(
        id = "order_fix_stratType",
        type = "text",
        readOnly = True,
        placeholder = "",
    )

    orderSymbol = dcc.Input(
        id = "order_fix_symbol",
        type = "text",
        readOnly = True,
        placeholder = "",
    )

    responseBody = html.Div([
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.P('Tipo Estrategia:', className='font-weight-bold'),
                        orderStratType
                    ]
                ),
                dbc.Col(
                    [
                        html.P('Simbolo:', className='font-weight-bold'),
                        orderSymbol
                    ]
                ),                
            ]
        ),
        html.P('Ejecutamos Fix para esta: ',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderOrderId,
    ])
    
    modal = html.Div(
        [
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Regenerar Orden", id = "modal_fixOrder")),
                    dbc.ModalBody(responseBody, id = "OrdenFixBody"),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Fix", id="modal_fixOrder_boton_fix", className="ms-auto", n_clicks=0
                            ),
                            dbc.Button(
                                "Close", id="modal_fixOrder_boton_close", className="ms-auto", n_clicks=0
                            )
                        ]
                    ),
                ],
                id="modal_fixOrder_main",
                is_open=False,
            ),
        ]
    )
    return modal

#Callback para actualizar tabla de ordenes en Strategy
@callback(
    Output({'role':'TableStrategyOrderDetails', 'strategy':'PentagramaRu', 'symbol': MATCH}, "children"),
    Input({'role': 'IntervalOrderTable', 'strategy':'PentagramaRu', 'symbol': MATCH}, 'n_intervals'),
    prevent_initial_call = True,
)
def actualizarTablaOrdenesStrategiesPenRu (n_intervals):
    if not ctx.triggered_id:
        raise PreventUpdate
    if globales.G_RTlocalData_.strategies_ == None:
        raise PreventUpdate
    logging.debug ('Actualizando tabla ordenes estrategia')
    symbol = ctx.triggered_id['symbol']

    estrategia = globales.G_RTlocalData_.strategies_.strategyGetStrategyBySymbolAndType (symbol, 'PentagramaRu')
    resp = layout_getStrategyPenRuTableOrders (estrategia, True)

    return resp

#Callback para actualizar grafica today
@callback(
    Output({'role': 'graphDetailsToday', 'strategy':'PentagramaRu', 'symbol': MATCH}, 'figure'),
    Input({'role': 'IntervalgraphToday', 'strategy':'PentagramaRu', 'symbol': MATCH}, 'n_intervals'),
    prevent_initial_call = True,
)
def actualizarFiguraTodayPenRu (n_intervals):
    if not ctx.triggered_id:
        raise PreventUpdate
    if globales.G_RTlocalData_.strategies_ == None:
        raise PreventUpdate

    symbol = ctx.triggered_id['symbol']
    estrategia = globales.G_RTlocalData_.strategies_.strategyGetStrategyBySymbolAndType (symbol, 'PentagramaRu')

    fig1 = layout_getFigureTodayPenRu (estrategia, True)

    #return  zonasFilaBorderDown, no_update, no_update
    return  fig1


# Callback para grabar info de zonas
@callback(
    Output({'role': 'ZoneButtonReload', 'strategy':'PentagramaRu', 'symbol': MATCH}, "n_clicks"),   # Dash obliga a poner un output. Uno que no se use
    Input({'role': 'ZoneButtonReload', 'strategy':'PentagramaRu', 'symbol': MATCH}, "n_clicks"),
    prevent_initial_call = True,
)
def reloadStrategyRuFiles(n_clicks):

    if n_clicks is None or (not ctx.triggered_id):
        raise PreventUpdate

    if not 'symbol' in ctx.triggered_id:
        raise PreventUpdate

    symbol = ctx.triggered_id['symbol']

    logging.info ("Actualización de los ficheros de estrategia Ruben (%s)", symbol)
    #globales.G_RTlocalData_.strategies_.strategyPentagramaRuObj_.strategyPentagramaRuReadFile ()
    globales.G_RTlocalData_.strategies_.strategyReload ('PentagramaRu', symbol)

    return  no_update

# Callback para fix
@callback(
    Output("order_fix_orderId", "value"),
    Output("order_fix_stratType", "value"),
    Output("order_fix_symbol", "value"),
    Output("modal_fixOrder_main", "is_open"),
    Input({'role': 'boton_fix', 'orderId': ALL, 'symbol': ALL}, "n_clicks"),
    Input("modal_fixOrder_boton_fix", "n_clicks"),
    Input("modal_fixOrder_boton_close", "n_clicks"),
    Input("order_fix_orderId", "value"),
    Input("order_fix_stratType", "value"),
    Input("order_fix_symbol", "value"),
    State("modal_fixOrder_main", "is_open"), 
    prevent_initial_call = True,
)
def fixStrategyRuOrdenes (n_button_open, n_button_fix, n_button_close, orderId, stratType, Symbol, open_status):

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


    logging.debug('Trigger %s', ctx.triggered_id)

    if ctx.triggered_id == "modal_fixOrder_boton_close":
        return None, None, None, False
    
    if ctx.triggered_id == "modal_fixOrder_boton_fix":
        
        #ahora hay que arreglar
        logging.info('[Orden (%s)] Fix esta orden desde GUI', str(orderId))

        stratType = 'PentagramaRu'

        data = {'orderId': orderId}
    
        try:
            result = globales.G_RTlocalData_.strategies_.strategyIndexFix (data)
            result = True
        except:
            logging.error ("Exception occurred", exc_info=True)

        return None, None, None, False
            

    if 'orderId' in ctx.triggered_id:
        orderId = int(ctx.triggered_id['orderId'])
        Symbol = ctx.triggered_id['symbol']
        stratType = 'PentagramaRu'
        return orderId, stratType, Symbol, True

# Callback para enable/disable cerrarPos
@callback(
    Output({'role': 'switch_cerrarPos', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),   # Dash obliga a poner un output.
    Input({'role': 'switch_cerrarPos', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"), 
    prevent_initial_call = True,
)
def switchStrategyCerrarPos(state):
    
    if not ctx.triggered_id:
        return no_update
    symbol = str(ctx.triggered_id.symbol)
    strategyType = 'PentagramaRu'

    if state:
        logging.info ('Estrategia [%s] del tipo: %s. CerrarPos Enabled', symbol, strategyType)
    else:
        logging.info ('Estrategia [%s] del tipo: %s. CerrarPos Disabled', symbol, strategyType)

    globales.G_RTlocalData_.strategies_.strategyCerrarPosiciones (symbol, strategyType, state)
    
    return no_update