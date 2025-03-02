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
import datetime
import utils

logger = logging.getLogger(__name__)

def createStratBoton ():
    boton = dbc.Button("CrearPentaRu", id={'role': 'boton_create_strat', 'stratType': 'PentagramaRu'}, className="text9-7 d-inline-block me-0", n_clicks=0)
    return boton

def insideModalsPentagramaRu ():
    modals = []

    modalFix = modal_ordenFix()
    modalAssume = modal_ordenAcknowledgeFilled()
    modalConfirm = modal_StrategyConfirmar()
    modalCreateStrat = modal_addStrategy()
    modalManualExec = modal_addManualExec()

    store1 = dcc.Store(id='memory-symbol')

    modals.append(modalFix)
    modals.append(modalCreateStrat)
    modals.append(modalConfirm)
    modals.append(modalAssume)
    modals.append(modalManualExec)
    modals.append(store1)

    return modals


def insideDetailsPentagramaRu (estrategia):
    # Y las tablas con ordenes

    symbol = estrategia['symbol']
    stratType = estrategia['type']

    # Caja que solo se muestra en pantalla pequeña:

    todayPnl = formatCurrency(estrategia['classObject'].strategyGetExecPnL()['PnL'])
    unrealNum = estrategia['classObject'].strategyGetExecPnLUnrealized()
    unrealNumFmt = formatCurrency(unrealNum)
    totalPnl = todayPnl + '/' + unrealNumFmt

    execToday = 'Na'
    execTotal = 'Na'
    execToday = estrategia['classObject'].pandas_.dbGetExecCountToday()
    execTotal = estrategia['classObject'].pandas_.dbGetExecCountAll()
    execString = str(execToday) + '/' + str(execTotal)

    caja_pnl_execs_contenido = html.Div(
        dbc.Row(
                [
                    html.Div("Execs:" + execString),
                    html.Div("Total PnL:" + totalPnl)
                ]
            ),
            className="text9-7",
        )

    caja_pnl_execs = dbc.Card(caja_pnl_execs_contenido, body=True)

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
        ], 
        id={'role': 'form_cerrarPos', 'strategy':'PentagramaRu', 'symbol': symbol},
        className="text9-7",
    )

    # Los botones

    breload_text = html.Div('Recarga', className="text9-7 d-inline-block")
    breload_icon = html.I(className="bi bi-file-earmark-arrow-up me-2 d-inline-block")
    breload_content = html.Span([breload_icon, breload_text])
    boton_reload = dbc.Button(breload_content, id={'role': 'ZoneButtonReload', 'strategy':'PentagramaRu', 'symbol': symbol}, className="text9-7 d-inline-block me-0", n_clicks=0)
    boton_reload_tip = dbc.Tooltip("Recargar estrategia desde fichero", target={'role': 'ZoneButtonReload', 'strategy':'PentagramaRu', 'symbol': symbol})
    
    bedit_text = html.Div('Editar', className="text9-7 d-inline-block")
    bedit_icon = html.I(className="bi bi-pencil-square me-2 d-inline-block")
    bedit_content = html.Span([bedit_icon, bedit_text])
    boton_update = dbc.Button(bedit_content, id={'role': 'ZoneButtonUpdate', 'strategy':'PentagramaRu', 'symbol': symbol}, className="text9-7 d-inline-block me-0", n_clicks=0)
    boton_update_tip = dbc.Tooltip("Editar la estrategia", target={'role': 'ZoneButtonUpdate', 'strategy':'PentagramaRu', 'symbol': symbol})
    
    bdelete_text = html.Div('Borrar', className="text9-7 d-inline-block")
    bdelete_icon = html.I(className="bi bi-trash me-2 d-inline-block")
    bdelete_content = html.Span([bdelete_icon, bdelete_text])
    boton_delete = dbc.Button(bdelete_content, id={'role': 'ZoneButtonBorrar', 'strategy':'PentagramaRu', 'symbol': symbol}, className="d-inline-block me-0", n_clicks=0)
    boton_delete_tip = dbc.Tooltip("Borrar la estrategia", target={'role': 'ZoneButtonBorrar', 'strategy':'PentagramaRu', 'symbol': symbol})
    
    botonesUp = html.Div(
        [
            boton_reload,
            boton_reload_tip,
            boton_update,
            boton_update_tip,
            boton_delete,
            boton_delete_tip
        ],
        className="d-grid gap-2 d-flex justify-content-end",
    )

    # Contenigo de caja
    
    contenido_caja = html.Div(
        dbc.Row(
                [
                    dbc.Col(grupo_switches, md=6),
                    dbc.Col(botonesUp, md=6)
                ]
            ),
        )

    caja_inicial_top = dbc.Card(contenido_caja, body=True)

    # Aquí hay que añadir lo de editar

    colapsar = layout_modifyStrat(symbol)

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
            className='text9-7',
        ),
        dcc.Interval(
            id={'role': 'IntervalOrderTable', 'strategy':'PentagramaRu', 'symbol': symbol},
            interval= random_wait, # in milliseconds
            n_intervals=0
        )
    ])

    # Boton para añadir ordenes ejecutadas perdidas:
    baddexec_text = html.Div('Añadir Exec', className="text9-7 d-inline-block")
    baddexec_icon = html.I(className="bi bi-trash me-2 d-inline-block")
    baddexec_content = html.Span([baddexec_icon, baddexec_text])
    boton_addExec = dbc.Button(baddexec_content, id={'role': 'ButtonAddExec', 'strategy':'PentagramaRu', 'symbol': symbol}, className="d-inline-block me-0", n_clicks=0)
    boton_addExec_tip = dbc.Tooltip("Añadir manualmente Execution que se haya pedido", target={'role': 'ButtonAddExec', 'strategy':'PentagramaRu', 'symbol': symbol})
    
    botonAddExec = html.Div(
        [
            boton_addExec,
            boton_addExec_tip
        ],
        className="d-grid gap-2 d-flex justify-content-end",
    )
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
                    caja_pnl_execs, className = 'd-block d-md-none mb-3'
            ),
            
            dbc.Row(
                    colapsar, className = 'mb-3'
            ),
            dbc.Row(
                [
                    dbc.Col(graphColumn1, 'md-6'),
                    dbc.Col(graphColumn2, 'md-6')
                ],  className = 'mb-3' 
            ),
            dbc.Row(
                [
                    botonAddExec,
                    html.Div(
                        tablaExecs, 
                        id={'role': 'TableExecs', 'strategy':'PentagramaRu', 'symbol': symbol},
                        className = 'text9-7',
                    ),
                ]
            ),
            dbc.Row(
                    graphComponentes, className = 'mb-3' 
            ),
            dbc.Row(
                    insideOrdenes,
            ), 
            #modal_ordenFix()
        ],
        id={'role': 'colapse_strategy', 'strategy':'PentagramaRu', 'symbol': symbol},
        is_open=False,
        className = 'mb-3'
    )

    return collapseDetails

def layout_getFigureHistoricoPenRu (estrategia):
    fig1 = go.Figure()
    symbol = estrategia['symbol']
    contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
    if not contrato:
        logging.error ("Error cargando grafico historico de %s. No tenemos el contrato cargado en RT_Data", symbol)
        return fig1
    if contrato['dbPandas'] == None:
        return fig1

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
    fig2 = go.Figure()
    if estrategia == fig2:
        return fig2

    symbol = estrategia['symbol']
    contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)

    if not contrato:
        logging.error ('Error cargando grafico de Hoy de %s. No tenemos el contrato cargado en RT_Data', symbol)
        return fig2
    if contrato['dbPandas'] == None:
        return fig2
    if (contrato['dbPandas'].toPrint == False) and (update == True):
        logging.debug ('Grafico no actualizado. No hay datos nuevos')
        return fig2

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

def layout_modifyStrat(symbol):

    estrategia = globales.G_RTlocalData_.strategies_.strategyGetStrategyBySymbolAndType (symbol, 'PentagramaRu')

    #data = globales.G_RTlocalData_.strategies_.strategyGetBuildParams('PentagramaRu', symbol)
    data = estrategia['classObject'].strategyGetBuildParams()

    qty = dcc.Input(
        id = {'role': 'strategy_update_qty', 'strategy':'PentagramaRu', 'symbol': symbol},
        type = "number",
        value = data['qty_row'],
    )

    nBuys = dcc.Input(
        id = {'role': 'strategy_update_nBuys', 'strategy':'PentagramaRu', 'symbol': symbol},
        type = "number",
        value = data['nBuys'],
    )

    nSells = dcc.Input(
        id = {'role': 'strategy_update_nSells', 'strategy':'PentagramaRu', 'symbol': symbol},
        type = "number",
        value = data['nSells'],
    )

    interSpace = dcc.Input(
        id = {'role': 'strategy_update_interSpace', 'strategy':'PentagramaRu', 'symbol': symbol},
        type = "number",
        value = data['interSpace'],
    )

    gain = dcc.Input(
        id = {'role': 'strategy_update_gain', 'strategy':'PentagramaRu', 'symbol': symbol},
        type = "number",
        value = data['gain'],
    )

    first = dcc.Input(
        id = {'role': 'strategy_update_first', 'strategy':'PentagramaRu', 'symbol': symbol},
        type = "number",
        value = data['start'],
    )

    slBuy = dcc.Input(
        id = {'role': 'strategy_update_slBuy', 'strategy':'PentagramaRu', 'symbol': symbol},
        type = "number",
        value = data['sl_buy'],
    )

    slSell = dcc.Input(
        id = {'role': 'strategy_update_slSell', 'strategy':'PentagramaRu', 'symbol': symbol},
        type = "number",
        value = data['sl_sell'],
    )

    fig1 = go.Figure()
    graphUpdateStrat = html.Div(
        dcc.Graph(
            id = {'role': 'strategy_update_graph', 'strategy':'PentagramaRu', 'symbol': symbol},
            animate = False,
            figure = fig1
        )
    )

    bpreview_text = html.Div('Preview', className="text9-7 d-inline-block")
    bpreview_icon = html.I(className="bi bi-eye me-2 d-inline-block")
    bpreview_content = html.Span([bpreview_icon, bpreview_text])
    boton_preview = dbc.Button(bpreview_content, id={'role': 'strategy_update_button_preview', 'strategy':'PentagramaRu', 'symbol': symbol}, className="text9-7 d-inline-block me-0", n_clicks=0)
    boton_preview_tip = dbc.Tooltip("Actualizar el graph con los parametros de entrada. Es importante para ver si está bien", target={'role': 'strategy_update_button_preview', 'strategy':'PentagramaRu', 'symbol': symbol})
    
    bcommit_text = html.Div('Ejecutar', className="text9-7 d-inline-block")
    bcommit_icon = html.I(className="bi bi-check2-square me-2 d-inline-block")
    bcommit_content = html.Span([bcommit_icon, bcommit_text])
    boton_commit = dbc.Button(bcommit_content, id={'role': 'strategy_update_button_commit', 'strategy':'PentagramaRu', 'symbol': symbol}, className="text9-7 d-inline-block me-0", n_clicks=0)
    boton_commit_tip = dbc.Tooltip("Ejecutar los cambios. Es importante comprobar con 'Preview' que están bien. Recargar en navegador al final", target={'role': 'strategy_update_button_commit', 'strategy':'PentagramaRu', 'symbol': symbol})
    
    breset_text = html.Div('Restaurar', className="text9-7 d-inline-block")
    breset_icon = html.I(className="bi bi-arrow-counterclockwise me-2 d-inline-block")
    breset_content = html.Span([breset_icon, breset_text])
    boton_reset = dbc.Button(breset_content, id={'role': 'strategy_update_button_reset', 'strategy':'PentagramaRu', 'symbol': symbol}, className="d-inline-block me-0", n_clicks=0)
    boton_reset_tip = dbc.Tooltip("Restaurar los parametros y dejarlos segun la estrategia actual", target={'role': 'strategy_update_button_reset', 'strategy':'PentagramaRu', 'symbol': symbol})
    
    botonesStrategyUpdate = html.Div(
        [
            boton_preview,
            boton_preview_tip,
            boton_reset,
            boton_reset_tip,
            boton_commit,
            boton_commit_tip
        ],
        className="d-grid gap-2 d-flex justify-content-end",
    )

    swTBD = dbc.Switch(id={'role': 'switchStratUpdateTBDView', 'strategy':'PentagramaRU', 'symbol': symbol}, className="d-inline-block", value = False)

    OrdersTableHeader = [
        html.Thead(
            html.Tr(
                [
                   html.Th("B/S"),
                   html.Th("Price"),
                   html.Th("TP"),
                   html.Th("SL"),
                   html.Th("Qty"),
                   html.Th(html.Span(["New/TDB", swTBD]), className="d-grid gap-2 d-flex justify-content-end"),
                   html.Th("Status"),
                ], style={'color':'#ffffff','background-color':'#636363'}
            )   
        )
    ]

    NewOrdersTable = dbc.Table(
        OrdersTableHeader, 
        id={'role':'strategy_update_table', 'strategy':'PentagramaRu', 'symbol': symbol},
        className="text9-7",
        bordered=True
    )
            
    stratUpdatePart = dbc.Collapse(
        [
            dbc.Card(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.P('Numero de BUY:',
                                        style={'margin-top': '8px', 'margin-bottom': '4px'},
                                        className='font-weight-bold'),
                                    nBuys,
                                    html.P('Numero de SELL:',
                                        style={'margin-top': '8px', 'margin-bottom': '4px'},
                                        className='font-weight-bold'),
                                    nSells,
                                    html.P('Precio (LMT) de la orden Parent de valor más alto:',
                                        style={'margin-top': '8px', 'margin-bottom': '4px'},
                                        className='font-weight-bold'),
                                    first,
                                    html.P('Espaciado del precio de ordenes Parents:',
                                        style={'margin-top': '8px', 'margin-bottom': '4px'},
                                        className='font-weight-bold'),
                                    interSpace,
                                ]
                            ),
                            dbc.Col(
                                [
                                    html.P('Qty:',
                                        style={'margin-top': '8px', 'margin-bottom': '4px'},
                                        className='font-weight-bold'),
                                    qty,
                                    html.P('Ganancia Take Profit:',
                                        style={'margin-top': '8px', 'margin-bottom': '4px'},
                                        className='font-weight-bold'),
                                    gain,
                                    html.P('Stop Loss BUY:',
                                        style={'margin-top': '8px', 'margin-bottom': '4px'},
                                        className='font-weight-bold'),
                                    slBuy,
                                    html.P('Stop Loss SELL:',
                                        style={'margin-top': '8px', 'margin-bottom': '4px'},
                                        className='font-weight-bold'),
                                    slSell,
                                ]
                            )
                        ], className = 'mb-3' 
                    ),
                    dbc.Row(
                        botonesStrategyUpdate, className = 'mb-3' 
                    ),
                    dbc.Row(
                        dbc.Alert("", className="mb-3" , color="primary", id={'role': 'StrategyUpdateAlert', 'strategy':'PentagramaRu', 'symbol': symbol},dismissable=True,is_open=False)
                    ),
                    dbc.Row(
                        html.Div(NewOrdersTable), className = 'mb-3' 
                    ),
                    dbc.Row(
                        html.Div(graphUpdateStrat)
                    )
                ],
                className = 'text9-7',
                body=True
            )   
        ], 
        id={'role': 'colapse_strategy_modify', 'strategy':'PentagramaRu', 'symbol': symbol},
        is_open=False,
    )

    return stratUpdatePart
    
    
def layout_getFigureLinesFromParams (contract, data = False):

    fig1 = go.Figure()

    nBuys = data['nBuys']
    nSells = data['nSells']
    interSpace = data['interSpace']
    gain = data['gain']
    first = data['start']
    sl_buy = data['sl_buy']
    sl_sell = data['sl_sell']

    if contract != None:
        df_comp = contract['dbPandas'].dbGetDataframeComp()
        longitud = len (df_comp.index)
        x_refer = df_comp.index
        fig1.add_trace(
            go.Candlestick(
                x=x_refer, 
                open=df_comp['open'], 
                high=df_comp['high'],
                low=df_comp['low'],
                close=df_comp['close'],
                hoverinfo='skip'
            ),
        )
    else:
        longitud = 10
        x_refer = list (range(10))

    value = first
    for n in range(nSells):
        tp = value - gain
        fig1.add_trace(go.Scatter(x=x_refer, y=[value]*longitud, mode="lines", line_color="gray", line_width=1, connectgaps = True, fill=None))
        fig1.add_trace(go.Scatter(x=x_refer, y=[tp]*longitud, mode="lines", line_dash='dash', line_width=1, line_color="gray", connectgaps = True, fill=None))
        value -= interSpace
    for n in range(nBuys):
        tp = value + gain
        fig1.add_trace(go.Scatter(x=x_refer, y=[value]*longitud, mode="lines", line_color="gray", line_width=1, connectgaps = True, fill=None))
        fig1.add_trace(go.Scatter(x=x_refer, y=[tp]*longitud, mode="lines", line_dash='dash', line_width=1, line_color="gray", connectgaps = True, fill=None))
        value -= interSpace

    fig1.add_trace(go.Scatter(x=x_refer, y=[sl_buy]*longitud, mode="lines", line_dash='dash', line_width=1, line_color="gray", connectgaps = True, fill=None))
    fig1.add_trace(go.Scatter(x=x_refer, y=[sl_sell]*longitud, mode="lines", line_dash='dash', line_width=1, line_color="gray", connectgaps = True, fill=None))

    if contract != None:    
        fig1.add_trace(
            go.Candlestick(
                x=df_comp.index, 
                open=df_comp['open'], 
                high=df_comp['high'],
                low=df_comp['low'],
                close=df_comp['close'],
                hoverinfo='skip'
            ),
        )

    fig1.update_yaxes(
        tickformat='.2f', 
    )

    fig1.update_layout(showlegend=False, 
                       font_size=10,
                       title_font_size=13,
                       xaxis_rangeslider_visible=False, 
                       yaxis={'side': 'right'} ,
                       title_text='Niveles Estrategia', 
                       title_x = 0.5,
                       title_xanchor = 'center',
                       margin=dict(l=0, r=0, t=40, b=40),
                       dragmode=False
    )

    return fig1

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
    
    modal = dbc.Modal(
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
    )
    return modal

def modal_ordenAcknowledgeFilled():

    orderOrderId = dcc.Input(
        id = "order_assumeFilled_orderId",
        type = "text",
        readOnly = True,
        placeholder = "",
    )

    orderStratType = dcc.Input(
        id = "order_assumeFilled_stratType",
        type = "text",
        readOnly = True,
        placeholder = "",
    )

    orderSymbol = dcc.Input(
        id = "order_assumeFilled_symbol",
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
        html.P('Asumimos que esta orden está Filled: ',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderOrderId,
    ])
    
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Orden Asumida como Filled", id = "modal_assumeFilledOrder")),
            dbc.ModalBody(responseBody, id = "OrdenFixBody"),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Fix", id="modal_assumeFilledOrder_boton_assume", className="ms-auto", n_clicks=0
                    ),
                    dbc.Button(
                        "Close", id="modal_assumeFilledOrder_boton_close", className="ms-auto", n_clicks=0
                    )
                ]
            ),
        ],
        id="modal_assumeFilledOrder_main",
        is_open=False,
    )
    return modal

def modal_addStrategy():

    # Aquí habria que añadir un id para el tipo de estrategia, y con un callback decidir el responseBody

    contratosAll = globales.G_RTlocalData_.contractGetListUnique()

    Symbol = dcc.Dropdown(
        options = contratosAll,
        id = "strategy_create_symbol",
    )

    Qty = dcc.Input(
        id = "strategy_create_qty",
        type = "number",
        placeholder = "1",
    )

    nBuys = dcc.Input(
        id = "strategy_create_nBuys",
        type = "number",
        placeholder = "0",
    )

    nSells = dcc.Input(
        id = "strategy_create_nSells",
        type = "number",
        placeholder = "0",
    )

    interSpace = dcc.Dropdown(
        options = [.250, .300, .350], 
        value = .250, 
        id = 'strategy_create_interSpace'
    )

    gain = dcc.Input(
        id = "strategy_create_gain",
        type = "number",
        placeholder = "0",
    )

    first = dcc.Input(
        id = "strategy_create_first",
        type = "number",
        placeholder = "0",
    )

    slBuy = dcc.Input(
        id = "strategy_create_slBuy",
        type = "number",
        placeholder = "0",
    )

    slSell = dcc.Input(
        id = "strategy_create_slSell",
        type = "number",
        placeholder = "0",
    )

    fig1 = go.Figure()
    graphCreateStrat = html.Div(
        dcc.Graph(
            id = "strategy_create_graph",
            animate = False,
            figure = fig1
        )
    )

    responseBody = html.Div([
        html.P('Simbolo Estrategia: ',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        Symbol,
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.P('Numero de BUY:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        nBuys,
                        html.P('Numero de SELL:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        nSells,
                        html.P('Primer LMT:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        first,
                        html.P('Espaciado:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        interSpace,
                    ]
                ),
                dbc.Col(
                    [
                        html.P('Qty:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        Qty,
                        html.P('Ganancia TP:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        gain,
                        html.P('Stop Loss BUY:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        slBuy,
                        html.P('Stop Loss SELL:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        slSell,
                    ]
                )
            ]
        ),
        dbc.Alert("", className="mt-2" , color="primary", id='modalStrategyCreateAlert',dismissable=True,is_open=False),
        html.Div(graphCreateStrat)
    ])
    
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Crear Estrategia", id = "modalStrategyCreateHeader")),
            dbc.ModalBody(responseBody, id = "modalStrategyCreateBody"),
            dbc.ModalFooter([
                dbc.Button(
                    "Preview", id="modalStrategyCreate_boton_show", className="ms-auto", n_clicks=0
                ),
                dbc.Button(
                    "Crear", id="modalStrategyCreate_boton_create", className="ms-auto", n_clicks=0
                ),
                dbc.Button(
                    "Close", id="modalStrategyCreate_boton_close", className="ms-auto", n_clicks=0
                )
            ]),
        ],
        id="modalStrategyCreate_main",
        is_open=False,
    )
    return modal

def modal_addManualExec():

    # Aquí habria que añadir un id para el tipo de estrategia, y con un callback decidir el responseBody

    timestamp_date = dcc.DatePickerSingle(
        id = "manual_exec_timestamp_date",
        date=datetime.datetime.now(),
    )

    timestamp_time = dcc.Input(
        type='time',
        id = "manual_exec_timestamp_time",
        value = '00:00'
    ) 

    orderStratType = dcc.Input(
        id = "manual_exec_stratType",
        type = "text",
        readOnly = True,
        placeholder = "",
    )

    orderSymbol = dcc.Input(
        id = "manual_exec_symbol",
        type = "text",
        readOnly = True,
        placeholder = "",
    )

    execId = dcc.Input(
        id = "manual_exec_execId",
        type = "text",
        placeholder = "0000ffff.ffff0000ff.01",
    )

    orderId = dcc.Input(
        id = "manual_exec_orderId",
        type = "number",
        placeholder = "0",
    )

    permId = dcc.Input(
        id = "manual_exec_permId",
        type = "number",
        placeholder = 999999999,
    )

    qty = dcc.Input(
        id = "manual_exec_qty",
        type = "number",
        placeholder = 1,
    )

    side = dcc.Dropdown(
        id = "manual_exec_side",
        options = ['BOT', 'SLD'], 
        value = 'BOT', 
    )

    realizedPnL = dcc.Input(
        id = "manual_exec_realPnL",
        type = "number",
        placeholder = 0,
    )

    commission = dcc.Input(
        id = "manual_exec_commission",
        type = "number",
        placeholder = 11.88,
    )

    fillPrice = dcc.Input(
        id = "manual_exec_fillPrice",
        type = "number",
        placeholder = 1.00,
    )


    responseBody = html.Div([
        html.P('Simbolo Estrategia: ',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderSymbol,
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.P('Timestamp:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        timestamp_date,
                        timestamp_time,
                        html.P('Estrategia:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        orderStratType,
                        html.P('ExecId:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        execId,
                        html.P('orderId:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        orderId,
                        html.P('permId:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        permId,
                    ]
                ),
                dbc.Col(
                    [
                        html.P('Qty:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        qty,
                        html.P('Side:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        side,
                        html.P('Fill Price:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        fillPrice,
                        html.P('Commission:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        commission,
                        html.P('Realized PnL:',
                            style={'margin-top': '8px', 'margin-bottom': '4px'},
                            className='font-weight-bold'),
                        realizedPnL,
                    ]
                )
            ]
        ),
    ])
    
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Añadir Exec Manualmente", id = "modalManualExecHeader")),
            dbc.ModalBody(responseBody, id = "modalManualExecBody"),
            dbc.ModalFooter([
                dbc.Button(
                    "Añadir Exec", id="modalManualExec_boton_create", className="ms-auto", n_clicks=0
                ),
                dbc.Button(
                    "Salir", id="modalManualExec_boton_close", className="ms-auto", n_clicks=0
                )
            ]),
        ],
        id="modalManualExec_main",
        is_open=False,
    )
    return modal

def modal_StrategyConfirmar():
    modal = dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Borrar estrategia", id = "modalStratConfirmarHeader")),
                    dbc.ModalBody("Seguro que quieres borrarla?", id = "modalStratConfirmarBody"),
                    dbc.ModalFooter([
                        dbc.Button(
                            "Aceptar", id="modalStratConfirmar_boton_accept", className="ms-auto", n_clicks=0
                        ),
                        dbc.Button(
                            "Close", id="modalStratConfirmar_boton_close", className="ms-auto", n_clicks=0
                        )
                    ]),
                ],
                id="modalStratConfirmar_main",
                is_open=False,
    )
    return modal

def getListaOrders (symbol):
    pass

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

# Callback para colapsar o mostrar filas Strategias
@callback(
    Output({'role': 'colapse_strategy_modify', 'strategy':'PentagramaRu', 'symbol': MATCH}, "is_open"),
    Input({'role': 'ZoneButtonUpdate', 'strategy':'PentagramaRu', 'symbol': MATCH}, "n_clicks"),
    State({'role': 'colapse_strategy_modify', 'strategy':'PentagramaRu', 'symbol': MATCH}, "is_open"),
    prevent_initial_call = True,
)
def toggle_colapse_strategy_edit(n_button, is_open):
    if n_button:
        return not is_open
    return is_open

    
# Callback para borrar strat
@callback(
    Output("modalStratConfirmar_main", "is_open"),
    Output("memory-symbol", "data"),
    Input({'role': 'ZoneButtonBorrar', 'strategy':'PentagramaRu', 'symbol': ALL}, "n_clicks"),
    Input("modalStratConfirmar_boton_accept", "n_clicks"),
    Input("modalStratConfirmar_boton_close", "n_clicks"),
    Input("memory-symbol", "data"),
    prevent_initial_call = True,
)
def DeleteStrat ( n_button_borrar, n_button_aceptar, n_button_cerrar, data):

    # Esto es por si las moscas
    #logging.info('Trigger 2 %s', ctx.triggered_id)
    #data = ""
    if (n_button_aceptar is None and n_button_borrar is None and n_button_cerrar is None) or (not ctx.triggered_id):
        raise PreventUpdate
    
    '''
    pageLoad = True
    for button in  n_button_borrar:
        if button != None:
            pageLoad = False
    if pageLoad:
        raise PreventUpdate
    '''
    
    logging.info('LLamando a borrar Estrategia. Trigger: %s', ctx.triggered_id)
    
    if 'role' in ctx.triggered_id and ctx.triggered_id['role'] == 'ZoneButtonBorrar':
        data = ctx.triggered_id['symbol']
        return True, data

    if ctx.triggered_id == "modalStratConfirmar_boton_close":
        return False, no_update

    if ctx.triggered_id == "modalStratConfirmar_boton_accept":
        symbol = data
        data_delete = {'symbol': symbol}
        try:
            result = globales.G_RTlocalData_.strategies_.strategyDeleteStrategy ('PentagramaRu', data_delete)
        except:
            logging.error ("Exception occurred borrando estrategia", exc_info=True)
            return False, no_update
        else:
            try:
                globales.G_RTlocalData_.strategies_.strategyInit ()
            except:
                logging.error ("Exception occurred cargando las estrategias", exc_info=True)
                return False, no_update

        data = None
        return False, data

    return no_update, no_update
    


# Callback para Crear Strat - Abrir Cerror
@callback(
    Output("modalStrategyCreate_main", "is_open", allow_duplicate=True),
    Input({'role': 'boton_create_strat', 'stratType': 'PentagramaRu'}, "n_clicks"),
    Input("modalStrategyCreate_boton_close", "n_clicks"),
    State("modalStrategyCreate_main", "is_open"), 
    prevent_initial_call = True,
)
def CreateStratRuOpenClose (n_button_open, n_button_close, open_status):

    # Esto es por si las moscas
    #logging.info('Trigger 2 %s', ctx.triggered_id)
    if (n_button_open is None and n_button_close is None) or (not ctx.triggered_id):
        raise PreventUpdate

    logging.info('LLamando a Crear Estrategia. Trigger: %s', ctx.triggered_id)

    if ctx.triggered_id == "modalStrategyCreate_boton_close":
        return False
    
    if 'stratType' in ctx.triggered_id:
        return True


# Callback para Crear Strat - Generar
@callback(
    Output("strategy_create_graph", "figure"),
    Output("modalStrategyCreate_main", "is_open"),
    Output("modalStrategyCreateAlert", "is_open"),
    Output("modalStrategyCreateAlert", "children"),
    Output("modalStrategyCreateAlert", "color"),
    Input("modalStrategyCreate_boton_show", "n_clicks"),
    Input("modalStrategyCreate_boton_create", "n_clicks"),
    Input("strategy_create_symbol", "value"),
    Input("strategy_create_qty", "value"),
    Input("strategy_create_nBuys", "value"),
    Input("strategy_create_nSells", "value"),
    Input("strategy_create_interSpace", "value"),
    Input("strategy_create_gain", "value"),
    Input("strategy_create_first", "value"),
    Input("strategy_create_slBuy", "value"),
    Input("strategy_create_slSell", "value"),
    prevent_initial_call = True,
)
def CreateStratRuGenerar (n_button_show, n_button_create, symbol, qty, nBuys, nSells, interSpace, gain, first, slBuy, slSell):

    # Esto es por si las moscas
    logging.debug('Trigger %s', ctx.triggered_id)
    
    if (n_button_show is None and n_button_create is None) or (not ctx.triggered_id):
        raise PreventUpdate

    data = {}
    data['symbol'] = symbol
    data['nBuys'] = nBuys
    data['nSells'] = nSells
    data['interSpace'] = interSpace
    data['gain'] = gain
    data['start'] = first
    data['qty_row'] = qty
    data['sl_buy'] = slBuy
    data['sl_sell'] = slSell

    if ctx.triggered_id == "modalStrategyCreate_boton_show":
        error_msg = ""
        try:
            nSells = int(nSells)
        except:
            error_msg = "Error en el nSells"
            logging.error ('Error en el nSells')
            #return no_update, True, no_update, no_update, no_update
            return no_update, True, True, error_msg, "danger"
        try:
            nBuys = int(nBuys)
        except:
            error_msg = "Error en el nBuys"
            logging.error ('Error en el nBuys')
            #return no_update, True, no_update, no_update, no_update
            return no_update, True, True, error_msg, "danger"
        try:
            qty = int(qty)
        except:
            error_msg = "Error en el qty"
            logging.error ('Error en el qty')
            #return no_update, True, no_update, no_update, no_update
            return no_update, True, True, error_msg, "danger"
        try:
            first = float(first)
        except:
            error_msg = "Error en el first"
            logging.error ('Error en el first')
            #return no_update, True, no_update, no_update, no_update
            return no_update, True, True, error_msg, "danger"
        try:
            gain = float(gain)
        except:
            error_msg = "Error en el gain"
            logging.error ('Error en el gain')
            #return no_update, True, no_update, no_update, no_update
            return no_update, True, True, error_msg, "danger"
        try:
            interSpace = float(interSpace)
        except:
            error_msg = "Error en el interSpace"
            logging.error ('Error en el interSpace')
            #return no_update, True, no_update, no_update, no_update
            return no_update, True, True, error_msg, "danger"
        try:
            slBuy = float(slBuy)
        except:
            error_msg = "Error en el slBuy"
            logging.error ('Error en el slBuy')
            #return no_update, True, no_update, no_update, no_update
            return no_update, True, True, error_msg, "danger"
        try:
            slSell = float(slSell)
        except:
            error_msg = "Error en el slSell"
            logging.error ('Error en el slSell')
            #return no_update, True, no_update, no_update, no_update
            return no_update, True, True, error_msg, "danger"

        contract = globales.G_RTlocalData_.contractGetBySymbol(symbol)

        fig1 = layout_getFigureLinesFromParams(contract, data)
        
        return fig1, no_update, False, "", "success"
    
    elif ctx.triggered_id == "modalStrategyCreate_boton_create":

        estrategia = globales.G_RTlocalData_.strategies_.strategyGetStrategyBySymbolAndType (symbol, 'PentagramaRu')
        if estrategia != None:
            #return no_update, no_update, no_update, no_update, no_update
            return no_update, no_update, True, "Este simbolo ya está en esta estrategia", "warning"
            #Esto quiere decir que ya hay una estrategia para este simbolo en Ru
        
        #ahora hay que crear todo
        try:
            result = globales.G_RTlocalData_.strategies_.strategyWriteNewStrategy ('PentagramaRu', data)
        except:
            logging.error ("Exception occurred añadiendo estrategia", exc_info=True)
            return no_update, True, True, "Error Creando Estrategia", "danger"
        else:
            try:
                globales.G_RTlocalData_.strategies_.strategyInit ()
            except:
                logging.error ("Exception occurred cargando las estrategias", exc_info=True)
                return no_update, True, True, "Error Creando Estrategia", "danger"

        #return no_update, True, True, header, body
        return no_update, True, True, "Estrategia creada correctamente. Recarga navegador", "success"

    else:
        raise PreventUpdate

# Callback para Editar Strat - Restore
@callback(
    Output({'role': 'strategy_update_qty', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),
    Output({'role': 'strategy_update_nBuys', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),
    Output({'role': 'strategy_update_nSells', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),
    Output({'role': 'strategy_update_interSpace', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),
    Output({'role': 'strategy_update_gain', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),
    Output({'role': 'strategy_update_first', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),
    Output({'role': 'strategy_update_slBuy', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),
    Output({'role': 'strategy_update_slSell', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),
    Input({'role': 'strategy_update_button_reset', 'strategy':'PentagramaRu', 'symbol': MATCH}, "n_clicks"),
    prevent_initial_call = True,
)
def UpdateStratRuRestore (n_button_restore):

    if (n_button_restore is None) or (not ctx.triggered_id):
        raise PreventUpdate

    if not 'symbol' in ctx.triggered_id:
        raise PreventUpdate

    symbol = ctx.triggered_id['symbol']
    estrategia = globales.G_RTlocalData_.strategies_.strategyGetStrategyBySymbolAndType (symbol, 'PentagramaRu')
    data = estrategia['classObject'].strategyGetBuildParams()

    nBuys = data['nBuys']
    nSells = data['nSells']
    interSpace = data['interSpace']
    gain = data['gain']
    first = data['start']
    qty = data['qty_row']
    slBuy = data['sl_buy']
    slSell = data['sl_sell']
        
    return qty, nBuys, nSells, interSpace, gain, first, slBuy, slSell

# Callback para Editar Strat
@callback(
    Output({'role': 'strategy_update_graph', 'strategy':'PentagramaRu', 'symbol': MATCH}, "figure"),
    Output({'role': 'strategy_update_table', 'strategy':'PentagramaRu', 'symbol': MATCH}, "children"),
    Output({'role': 'StrategyUpdateAlert', 'strategy':'PentagramaRu', 'symbol': MATCH}, "is_open"),
    Output({'role': 'StrategyUpdateAlert', 'strategy':'PentagramaRu', 'symbol': MATCH}, "children"),
    Output({'role': 'StrategyUpdateAlert', 'strategy':'PentagramaRu', 'symbol': MATCH}, "color"),
    Input({'role': 'strategy_update_button_preview', 'strategy':'PentagramaRu', 'symbol': MATCH}, "n_clicks"),
    Input({'role': 'strategy_update_button_commit', 'strategy':'PentagramaRu', 'symbol': MATCH}, "n_clicks"),
    Input({'role': 'switchStratUpdateTBDView', 'strategy':'PentagramaRU', 'symbol': MATCH}, "value"),
    Input({'role': 'strategy_update_qty', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),
    Input({'role': 'strategy_update_nBuys', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),
    Input({'role': 'strategy_update_nSells', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),
    Input({'role': 'strategy_update_interSpace', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),
    Input({'role': 'strategy_update_gain', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),
    Input({'role': 'strategy_update_first', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),
    Input({'role': 'strategy_update_slBuy', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),
    Input({'role': 'strategy_update_slSell', 'strategy':'PentagramaRu', 'symbol': MATCH}, "value"),
    prevent_initial_call = True,
)
def UpdateStratRuPreview (n_button_preview, n_button_commit, switchTBD, qty, nBuys, nSells, interSpace, gain, first, slBuy, slSell):

    # Esto es por si las moscas
    logging.info('Trigger %s', ctx.triggered_id)

    if (n_button_preview is None and n_button_preview is None) or (not ctx.triggered_id):
        raise PreventUpdate
    
    logging.info ('Preview de Strat Updata: %s', ctx.triggered_id)

    if 'role' in ctx.triggered_id and ctx.triggered_id['role'] in ['strategy_update_button_preview', 'switchStratUpdateTBDView']:
        symbol = ctx.triggered_id['symbol']

        logging.info ('Preview de Strat Updata: %s', symbol)

        data = {}
        data['symbol'] = symbol
        data['nBuys'] = nBuys
        data['nSells'] = nSells
        data['interSpace'] = interSpace
        data['gain'] = gain
        data['start'] = first
        data['qty_row'] = qty
        data['sl_buy'] = slBuy
        data['sl_sell'] = slSell

        estrategia = globales.G_RTlocalData_.strategies_.strategyGetStrategyBySymbolAndType (symbol, 'PentagramaRu')
        contract = globales.G_RTlocalData_.contractGetBySymbol(symbol)
        fig1 = layout_getFigureLinesFromParams(contract, data)

        swTBD = dbc.Switch(id={'role': 'switchStratUpdateTBDView', 'strategy':'PentagramaRU', 'symbol': symbol}, className="d-inline-block", value = switchTBD)

        NewOrdersTableHeader = [
            html.Thead(
                html.Tr(
                    [
                       html.Th("B/S"),
                       html.Th("Price"),
                       html.Th("TP"),
                       html.Th("SL"),
                       html.Th("Qty"),
                       html.Th(html.Span(["New/TDB", swTBD]), className="d-grid gap-2 d-flex justify-content-end"),
                       html.Th("Status"),
                    ], style={'color':'#ffffff','background-color':'#636363'}
                )   
            )
        ]
    
        try:
            lista_orderblocks = estrategia['classObject'].strategyGetOrdersDataFromParams(data)
        except:
            logging.error ("Exception pidiendo las ordenes", exc_info=True)
            alert_msg = "Error calculando ordenes nuevas"
            alert_color = 'danger'
            return no_update, no_update, True, alert_msg, alert_color

        NewOrdersTableContent = []

        for orderblock in lista_orderblocks:
            backgroundColorRow = '#ffffff'
            if orderblock['TBD'] == 'TBD':
                backgroundColorRow = '#d6bfba' # TDB
                if not switchTBD:
                    continue
            if orderblock['TBD'] == 'New':
                backgroundColorRow = '#c1c2c9' # New

            NewOrdersTableRow = html.Tr(
                [
                    html.Td(orderblock['B_S'], style={'background-color':'transparent'}), 
                    html.Td(orderblock['Price'], style={'background-color':'transparent'}), 
                    html.Td(orderblock['PrecioTP'], style={'background-color':'transparent'}), 
                    html.Td(orderblock['PrecioSL'], style={'background-color':'transparent'}), 
                    html.Td(orderblock['Qty'], style={'background-color':'transparent'}), 
                    html.Td(orderblock['TBD'], style={'background-color':'transparent'}), 
                    html.Td(orderblock['Status'], style={'background-color':'transparent'}), 
                ], 
                style={'color':'#000000','background-color':backgroundColorRow},
            )

            NewOrdersTableContent.append(NewOrdersTableRow)
            NewOrdersTableBody = [html.Tbody(NewOrdersTableContent)]


        NewOrdersTable = NewOrdersTableHeader + NewOrdersTableBody

        alert_msg = "Preview generado correctamente"
        alert_color = 'success'

        return fig1, NewOrdersTable, True, alert_msg, alert_color

    if 'role' in ctx.triggered_id and ctx.triggered_id['role'] in ['strategy_update_button_commit']:
        symbol = ctx.triggered_id['symbol']
        data = {}
        data['symbol'] = symbol
        data['nBuys'] = nBuys
        data['nSells'] = nSells
        data['interSpace'] = interSpace
        data['gain'] = gain
        data['start'] = first
        data['qty_row'] = qty
        data['sl_buy'] = slBuy
        data['sl_sell'] = slSell

        error = False
        alert_msg = ""
        alert_color = 'danger'

        estrategia = globales.G_RTlocalData_.strategies_.strategyGetStrategyBySymbolAndType (symbol, 'PentagramaRu')
        
        ret = estrategia['classObject'].strategyActualizaZonesDesdeGUI(data)
        alert_msg = ret['alert_msg']
        alert_color = ret['alert_color']

        return no_update, no_update, True, alert_msg, alert_color


    return no_update, no_update, no_update, no_update, no_update


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

# Callback para assumeFilled
@callback(
    Output("order_assumeFilled_orderId", "value"),
    Output("order_assumeFilled_stratType", "value"),
    Output("order_assumeFilled_symbol", "value"),
    Output("modal_assumeFilledOrder_main", "is_open"),
    Input({'role': 'boton_assume', 'orderId': ALL, 'symbol': ALL}, "n_clicks"),
    Input("modal_assumeFilledOrder_boton_assume", "n_clicks"),
    Input("modal_assumeFilledOrder_boton_close", "n_clicks"),
    Input("order_assumeFilled_orderId", "value"),
    Input("order_assumeFilled_stratType", "value"),
    Input("order_assumeFilled_symbol", "value"),
    State("modal_assumeFilledOrder_main", "is_open"), 
    prevent_initial_call = True,
)
def assumeStrategyRuOrdenes (n_button_open, n_button_assume, n_button_close, orderId, stratType, Symbol, open_status):

    # Esto es por si las moscas
    if not ctx.triggered_id:
        raise PreventUpdate
    
    # Esto es por si las moscas
    pageLoad = True
    for button in  n_button_open:
        if button != None:
            pageLoad = False
    if n_button_assume:
        pageLoad = False
    if n_button_close:
        pageLoad = False
    if pageLoad:
        raise PreventUpdate


    logging.info('Trigger %s', ctx.triggered_id)

    if ctx.triggered_id == "modal_assumeFilledOrder_boton_close":
        return None, None, None, False
    
    if ctx.triggered_id == "modal_assumeFilledOrder_boton_assume":
        
        #ahora hay que arreglar
        logging.info('[Orden (%s)] Asumir Filled para esta orden desde GUI', str(orderId))
        data = {'orderId': orderId}

        stratType = 'PentagramaRu'

        try:
            result = globales.G_RTlocalData_.strategies_.strategyAssumeError (data)
            result = True
        except:
            logging.error ("Exception occurred", exc_info=True)

        return None, None, None, False
            
    orderId = None

    if 'orderId' in ctx.triggered_id:
        orderId = int(ctx.triggered_id['orderId'])
        Symbol = ctx.triggered_id['symbol']
        stratType = 'PentagramaRu'
        return orderId, stratType, Symbol, True

# Callback para añador exec manualmente
@callback(
    Output("manual_exec_orderId", "value"),
    Output("manual_exec_stratType", "value"),
    Output("manual_exec_symbol", "value"),
    Output("manual_exec_execId", "value"),
    Output("manual_exec_permId", "value"),
    Output("manual_exec_qty", "value"),
    Output("manual_exec_side", "value"),
    Output("manual_exec_realPnL", "value"),
    Output("manual_exec_commission", "value"),
    Output("manual_exec_fillPrice", "value"),
    Output("manual_exec_timestamp_date", "date"),
    Output("manual_exec_timestamp_time", "value"),
    Output("modalManualExec_main", "is_open"),
    Input({'role': 'ButtonAddExec', 'strategy': ALL, 'symbol': ALL}, "n_clicks"),
    Input("modalManualExec_boton_create", "n_clicks"),
    Input("modalManualExec_boton_close", "n_clicks"),
    Input("manual_exec_orderId", "value"),
    Input("manual_exec_stratType", "value"),
    Input("manual_exec_symbol", "value"),
    Input("manual_exec_execId", "value"),
    Input("manual_exec_permId", "value"),
    Input("manual_exec_qty", "value"),
    Input("manual_exec_side", "value"),
    Input("manual_exec_realPnL", "value"),
    Input("manual_exec_commission", "value"),
    Input("manual_exec_fillPrice", "value"),
    Input("manual_exec_timestamp_date", "date"),
    Input("manual_exec_timestamp_time", "value"),
    State("modalManualExec_main", "is_open"), 
    prevent_initial_call = True,
)
def addManualExec (n_button_open, n_button_add, n_button_close, orderId, stratType, symbol, execId, permId, qty, side, realPnL, commission, fillPrice, timestamp_date, timestamp_time, open_status):

    # Esto es por si las moscas
    if not ctx.triggered_id:
        raise PreventUpdate
    
    if ctx.triggered_id == "modalManualExec_boton_close":
        logging.info('Trigger %s', ctx.triggered_id)
        return None, None, None, None, None, None, None, None, None, None, None, None, False
    
    if ctx.triggered_id == "modalManualExec_boton_create":
        logging.info('Trigger %s', ctx.triggered_id)
        #ahora hay que añadir la exec
        #timestamp_date = datetime.datetime.strptime(timestamp_date, '%Y-%m-%dT%H:%M:%S.%f')
        timestamp_date = datetime.datetime.strptime(timestamp_date, '%Y-%m-%d')
        try:
            hour = int(timestamp_time[0:2])
        except:
            hour = 18
        try:
            minute = int(timestamp_time[3:])
        except:
            minute = 0
        timestamp_date = timestamp_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        timestamp_date = utils.date2local (timestamp_date)

        try:
            qty = float(qty)
        except:
            qty = 1.0
        try:
            realPnL = float(realPnL)
        except:
            realPnL = 0.0
        try:
            permId = int (permId)
        except:
            permId = 999999999
        try:
            fillPrice = float (fillPrice)
        except:
            fillPrice = 0.0

        logging.info ('Estrategia [%s] del tipo: %s. Añadimos Exec desde GUI:', symbol, stratType)
        logging.info ('     orderId: %s', orderId)
        logging.info ('     permId: %s', permId)
        logging.info ('     execId: %s', execId)
        logging.info ('     qty: %s', qty)
        logging.info ('     side: %s', side)
        logging.info ('     realPnL: %s', realPnL)
        logging.info ('     commission: %s', commission)
        logging.info ('     fillPrice: %s', fillPrice)
        logging.info ('     timestamp date: %s', timestamp_date)
        
        data = {}
        data['symbol'] = symbol
        data['stratType'] = stratType
        data['timestamp'] = timestamp_date
        data['ExecId'] = execId
        data['OrderId'] = orderId
        data['PermId'] = permId
        data['Quantity'] = qty
        data['Side'] = side 
        data['RealizedPnL'] = realPnL
        data['Commission'] = commission
        data['FillPrice'] = fillPrice

        try:
            result = globales.G_RTlocalData_.strategies_.strategyExecAddManual (data)
            result = True
        except:
            logging.error ("Exception occurred", exc_info=True)

        return None, None, None, None, None, None, None, None, None, None, None, None, False
            
    if 'role' in ctx.triggered_id:
        logging.info('Trigger %s', ctx.triggered_id)
        symbol = ctx.triggered_id['symbol']
        stratType = 'PentagramaRu'
        execId = '0000ffff.ffff0000ff.01'
        permId = 9999999
        qty = 1
        side = 'BOT'
        realPnL = 0.0
        commission = 11.88
        #fillPrice = 0.0
        date = datetime.date.today()
        time = '18:00'
        return None, stratType, symbol, execId, permId, qty, side, realPnL, commission, fillPrice, date, time, True
    raise PreventUpdate

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