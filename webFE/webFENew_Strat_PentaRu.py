from webFE.webFENew_Utils import formatCurrency, layout_getFigureHistorico, layout_getStrategyPenRuTableOrders, layout_getFigura_split, layout_getFigureToday
from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
from dash import html
from dash import dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import dash_table
from dash.dash_table.Format import Format, Group, Prefix, Scheme, Symbol
import globales
import logging
import random

logger = logging.getLogger(__name__)

def insideDetailsPentagramaRu (estrategia):
    # Y las tablas con ordenes

    symbol = estrategia['symbol']
    stratType = estrategia['type']

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
        ], id={'role': 'form_cerrarPos', 'strategy':'PentagramaRu', 'symbol': symbol}
    )

    # El boton de recarga

    boton_reload = dbc.Button("Recargar desde Fichero", id={'role': 'ZoneButtonReload', 'strategy':'PentagramaRu', 'symbol': symbol}, className="me-2", n_clicks=0)

    # Contenigo de caja
    
    contenido_caja = html.Div(
        dbc.Row(
                [
                    dbc.Col(grupo_switches, width=9),
                    dbc.Col(boton_reload, width=3)
                ]
            ),
        )

    caja_inicial_top = dbc.Card(contenido_caja, body=True)

    # Figura OHCL Comp

    fig1 = layout_getFigureHistoricoPenRu(estrategia)   # Lo tengo en una funcion para que sea facil actualizar
    graphColumn1 = html.Div(
        dcc.Graph(
            id={'role': 'graphDetailsComp', 'strategy': stratType, 'symbol': symbol},
            animate = False,
            figure = fig1
        )
    )

    # Figura Today

    random_wait = random.randint(0,1000) + 10000
    fig2 = layout_getFigureTodayPenRu(estrategia)   # Lo tengo en una funcion para que sea facil actualizar
    graphColumn2 = html.Div([
        dcc.Graph(
            id={'role': 'graphDetailsToday', 'strategy': stratType, 'symbol': symbol},
            animate = False,
            figure = fig2
        ),
        dcc.Interval(
            id={'role': 'IntervalgraphToday', 'strategy': stratType, 'symbol': symbol},
            interval= random_wait, # in milliseconds
            n_intervals=0
        )
    ])

    # Figura Split
        
    fig3 = layout_getFigura_split(symbol)   # Lo tengo en una funcion para que sea facil actualizar
    graphColumn3 = html.Div([
        dcc.Graph(
            id={'role': 'graphDetailsSpread', 'strategy': stratType, 'symbol': symbol},
            animate = False,
            figure = fig3
        )
    ])
    switch_compon_base = html.Div([
        dbc.Switch(
            id={'role': 'switch_componentes_base', 'strategy':stratType, 'symbol': symbol},
            label="Inicio a cero",
            value=False,
            className = 'mt-0 mt-md-5' 
        )],
        id={'role': 'switch_componentes_form', 'strategy':stratType, 'symbol': symbol},
    )

    graphComponentes = [
        dbc.Col(graphColumn3, md=10),
        dbc.Col(switch_compon_base, md=2)
    ]
 

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
    if len(df_execs) > 0:
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
                    dbc.Col(graphColumn1, 'md-6'),
                    dbc.Col(graphColumn2, 'md-6')
                ],  className = 'mb-3' 
            ),
            dbc.Row(
                html.Div(
                    tablaExecs, 
                    id={'role': 'TableExecs', 'strategy':'PentagramaRu', 'symbol': symbol},
                ),
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
    contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
    if not contrato:
        logging.error ("Error cargando grafico historico de %s. No tenemos el contrato cargado en RT_Data", symbol)
        return no_update
    if contrato['dbPandas'] == None:
        return no_update

    df_comp = contrato['dbPandas'].dbGetDataframeComp()

    fig1 = layout_getFigureHistorico(contrato)  # de Utils
    fig1 = addZonesLinesHistoricoRu (fig1, estrategia, df_comp)

    return fig1


def addZonesLinesHistoricoRu (fig1, estrategia, df_comp):
    limitList= []
    for zone in estrategia['classObject'].zones_: 

        ordenMain = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderId_)
        ordenSL = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderIdSL_)
        ordenTP = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderIdTP_)

        if zone['orderBlock'].Price_ not in limitList:
            zoneborder = [zone['orderBlock'].Price_] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_color="gray", line_width=1, hoverinfo='skip', connectgaps = True, fill=None), secondary_y=True)
            limitList.append(zone['orderBlock'].Price_)
        if zone['orderBlock'].PrecioSL_ not in limitList:
            zoneborder = [zone['orderBlock'].PrecioSL_] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_dash='dash', line_color="gray", hoverinfo='skip', line_width=1, connectgaps = True, fill=None), secondary_y=True)
            limitList.append(zone['orderBlock'].PrecioSL_)
        if zone['orderBlock'].PrecioTP_ not in limitList:
            zoneborder = [zone['orderBlock'].PrecioTP_] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_dash='dash', line_color="gray", hoverinfo='skip', line_width=1, connectgaps = True, fill=None), secondary_y=True)
            limitList.append(zone['orderBlock'].PrecioTP_)


    return fig1

def layout_getFigureTodayPenRu (estrategia, update = False):
    if estrategia == None:
        return no_update

    symbol = estrategia['symbol']
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
    LastPrice = None
    if len(dfToday.index) > 0:
        LastPrice = dfToday['close'].iloc[-1]

    fig2 = layout_getFigureToday(contrato)
    fig2 = addZonesLinesTodayRu (fig2, estrategia, dfToday)

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
                    fig2.add_trace(go.Scatter(x=dfToday.index, y=zoneborder, mode="lines", line_color="gray", line_width=1, hoverinfo='skip', connectgaps = True, fill=None))
                    limitList.append(zone['orderBlock'].Price_)
        if zone['orderBlock'].PrecioSL_ not in limitList:
            if ordenSL != None and ordenSL['params'] != None and 'status' in ordenSL['params']:
                if ordenSL['params']['status'] == 'Submitted':
                    zoneborder = [zone['orderBlock'].PrecioSL_] * len (dfToday.index)
                    fig2.add_trace(go.Scatter(x=dfToday.index, y=zoneborder, mode="lines", line_dash='dash', line_color="gray", hoverinfo='skip', line_width=1, connectgaps = True, fill=None))
                    limitList.append(zone['orderBlock'].PrecioSL_)
        if zone['orderBlock'].PrecioTP_ not in limitList:
            if ordenTP != None and ordenTP['params'] != None and 'status' in ordenTP['params']:
                if ordenTP['params']['status'] == 'Submitted':
                    zoneborder = [zone['orderBlock'].PrecioTP_] * len (dfToday.index)
                    fig2.add_trace(go.Scatter(x=dfToday.index, y=zoneborder, mode="lines", line_dash='dash', line_color="gray", hoverinfo='skip', line_width=1, connectgaps = True, fill=None))
                    limitList.append(zone['orderBlock'].PrecioTP_)

    return fig2
    
def modal_ordenFix():

    orderOrderId = dcc.Input(
        id = "order_fix_orderId",
        type = "text",
        readOnly = True,
        placeholder = "",
    )

    orderOrderIntId = dcc.Input(
        id = "order_fix_orderIntId",
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

        html.P('Su Internal Id es: ',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderOrderIntId,
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

    if resp == None:
        resp = no_update

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
    Output("order_fix_orderIntId", "value"),
    Output("order_fix_stratType", "value"),
    Output("order_fix_symbol", "value"),
    Output("modal_fixOrder_main", "is_open"),
    Input({'role': 'boton_fix', 'orderId': ALL, 'symbol': ALL}, "n_clicks"),
    Input({'role': 'boton_fix', 'orderIntId': ALL, 'symbol': ALL}, "n_clicks"),
    Input("modal_fixOrder_boton_fix", "n_clicks"),
    Input("modal_fixOrder_boton_close", "n_clicks"),
    Input("order_fix_orderId", "value"),
    Input("order_fix_orderIntId", "value"),
    Input("order_fix_stratType", "value"),
    Input("order_fix_symbol", "value"),
    State("modal_fixOrder_main", "is_open"), 
    prevent_initial_call = True,
)
def fixStrategyRuOrdenes (n_button_open, n_button_open2, n_button_fix, n_button_close, orderId, orderIntId, stratType, Symbol, open_status):

    # Esto es por si las moscas
    if not ctx.triggered_id:
        raise PreventUpdate
    
    # Esto es por si las moscas
    pageLoad = True
    for button in  n_button_open:
        if button != None:
            pageLoad = False
    for button in  n_button_open2:
        if button != None:
            pageLoad = False
    if pageLoad:
        raise PreventUpdate


    logging.info('Trigger %s', ctx.triggered_id)

    if ctx.triggered_id == "modal_fixOrder_boton_close":
        return None, None, None, None, False
    
    if ctx.triggered_id == "modal_fixOrder_boton_fix":
        
        #ahora hay que arreglar
        if orderId != 'None' and orderId != None:
            logging.info('[Orden (%s)] Fix esta orden desde GUI', str(orderId))
            data = {'orderId': orderId}
        else:
            logging.info('[Orden (%s)] Fix esta orden desde GUI', str(orderIntId))
            data = {'orderIntId': orderIntId}

        stratType = 'PentagramaRu'

        try:
            result = globales.G_RTlocalData_.strategies_.strategyIndexFix (data)
            result = True
        except:
            logging.error ("Exception occurred", exc_info=True)

        return None, None, None, None, False
            
    orderId = None
    orderIntId = None

    if 'orderId' in ctx.triggered_id:
        orderId = int(ctx.triggered_id['orderId'])
        Symbol = ctx.triggered_id['symbol']
        stratType = 'PentagramaRu'
        return orderId, orderIntId, stratType, Symbol, True
    elif 'orderIntId' in ctx.triggered_id:
        orderIntId = ctx.triggered_id['orderIntId']
        Symbol = ctx.triggered_id['symbol']
        stratType = 'PentagramaRu'
        return orderId, orderIntId, stratType, Symbol, True

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

#Callback para actualizar grafica today
@callback(
    Output({'role': 'graphDetailsSpread', 'strategy': MATCH, 'symbol': MATCH}, 'figure'),
    Input ({'role': 'switch_componentes_base', 'strategy':MATCH, 'symbol': MATCH}, 'value'),
    prevent_initial_call = True,
)
def actualizarFiguraComponentes (state_base):
    if not ctx.triggered_id:
        raise PreventUpdate
    if globales.G_RTlocalData_.strategies_ == None:
        raise PreventUpdate

    symbol = ctx.triggered_id['symbol']
  
    fig3 = layout_getFigura_split(symbol, state_base)

    #return  zonasFilaBorderDown, no_update, no_update
    return  fig3