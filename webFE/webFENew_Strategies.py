from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import webFE.webFENew_Strat_PentaRu
from webFE.webFENew_Utils import formatCurrency
import globales
import logging
import random

logger = logging.getLogger(__name__)

def layout_strategies_tab():

    #strategyPentagrama_ = globales.G_RTlocalData_.strategies_.strategyPentagramaObj_.strategyPentagramaGetAll()
    #strategyPentagramaRu_ = globales.G_RTlocalData_.strategies_.strategyPentagramaRuObj_.strategyPentagramaRuGetAll()
    strategyList = globales.G_RTlocalData_.strategies_.strategyGetAll()

    #{'symbol': symbol, 'type': type, 'classObject': classObject}

    #itemZG = 0 # Sirve para dar identidades unicas a las zonas
    ContentItems = []
    ####################################
    # Preparacion de Tab de Estratgias

    # Cabecera

    logging.debug ('Empiezo a calcular tab')

    tabEstrategias = [
            dbc.Row(
                [

                    dbc.Col(
                        html.P("Lista de Estrategias", className='text-left mb-0 text-secondary display-6'),
                        className = 'ps-0',
                        width = 9
                    ),
                    dbc.Col(
                        html.Div(
                            dbc.Button("Reload Todas", id={'role': 'ZoneButtonReloadAll'}, className="me-0", n_clicks=0),
                            className="text-end"
                        ),
                        className = 'pe-0',
                        width = 3
                    ),
                ],
                className = 'mb-4',
            ),
            dbc.Row(
                [
                    html.Hr()
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(html.Div("Symbol"), className = 'bg-primary mr-1', width = 3),
                    dbc.Col(html.Div("Pos"), className = 'bg-primary mr-1', width = 1),
                    dbc.Col(html.Div("Buy/Sell/Last"), className = 'bg-primary mr-1', width = 2),
                    dbc.Col(html.Div("PnL (daily/real/unreal)"), className = 'bg-primary mr-1', width = 3),
                    dbc.Col(html.Div("Exec (Hoy/Total)"), className = 'bg-primary', width = 2),
                    dbc.Col(html.Div("Enabled"), className = 'bg-primary', width = 1),
                ], className = 'mb-3 text-white'
                ),
            ]

    # Ahora cada una de las lineas

    for estrategia in strategyList:
        symbol = estrategia['symbol']
        stratType = estrategia['type']
        
        random_wait = random.randint(0,2000) + 4000
        headerRowInn = layout_getStrategyHeader (estrategia, False)
        
        headerRow = html.Div(
            [
                html.Div(
                    headerRowInn, id ={'role':'estrategia_header', 'strategy': stratType, 'symbol': symbol}
                ),
                dcc.Interval(
                    id={'role': 'IntervalHeaderStrategy', 'strategy': stratType, 'symbol': symbol},
                    interval= random_wait, # in milliseconds
                    n_intervals=0
                )
            ]
        )

        logging.debug ('Ya tengo la cabecera')

        # Los dos graficos
        fig1 = layout_getFigura1(estrategia)   # Lo tengo en una funcion para que sea facil actualizar
        graphColumn1 = html.Div(
            dcc.Graph(
                    id={'role': 'graphDetailsComp', 'strategy': stratType, 'symbol': symbol},
                    animate = False,
                    figure = fig1
            )
        )


        logging.debug ('Ya tengo la fig1')
        
        random_wait = random.randint(0,1000) + 10000

        fig2 = layout_getFigura2(estrategia)   # Lo tengo en una funcion para que sea facil actualizar
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
        
        fig3 = layout_getFigura3(estrategia)   # Lo tengo en una funcion para que sea facil actualizar
        graphColumn3 = html.Div([
            dcc.Graph(
                    id={'role': 'graphDetailsSpread', 'strategy': stratType, 'symbol': symbol},
                    animate = False,
                    figure = fig3
            )
        ])
        switch_compon_base = dbc.Switch(
            id={'role': 'switch_componentes_base', 'strategy':stratType, 'symbol': symbol},
            label="Inicio a cero",
            value=False,
            className = 'mt-5' 
        )

        graphComponentes = [
            dbc.Col(graphColumn3, width=10),
            dbc.Col(switch_compon_base, width=2)
        ]

        logging.debug ('Ya tengo la fig2')

        collapseDetails = insideDetailsStrategia (estrategia, graphColumn1, graphColumn2, graphComponentes)

        # Lo añadimos a la pagina/tab:

        tabEstrategias.append(headerRow)
        tabEstrategias.append(collapseDetails)    

        logging.debug ('Ya tengo todo')    

    return tabEstrategias


def layout_getFigura1(estrategia):
    stratType = estrategia['type']
    fig1 = None
    if stratType == 'PentagramaRu':
        fig1 = webFE.webFENew_Strat_PentaRu.layout_getFigureHistoricoPenRu (estrategia)

    return fig1


def layout_getFigura2(estrategia):
    stratType = estrategia['type']
    fig2 = None
    if stratType == 'PentagramaRu':
        fig2 = webFE.webFENew_Strat_PentaRu.layout_getFigureTodayPenRu (estrategia)

    return fig2


def layout_getFigura3(estrategia, base = False):
    stratType = estrategia['type']
    fig3 = None

    symbolSpread = estrategia['symbol']
    spread_list = globales.G_RTlocalData_.appObj_.contractCode2list(symbolSpread)
    spread_list.append ({'action':'BAG', 'ratio': 1, 'code': symbolSpread})

    fig3 = go.Figure()
    fig3 = make_subplots(specs=[[{"secondary_y": True}]])

    for comp in spread_list:
        symbol = comp['code']
        contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
        if not contrato:
            logging.error ("Error cargando grafico historico de %s. No tenemos el contrato cargado en RT_Data", symbol)
            break
        if contrato['dbPandas']:
            df_comp = contrato['dbPandas'].dbGetDataframeComp()
            if base:
                base_level = df_comp.iloc[0]["close"]
            else:
                base_level = 0
            if comp ['action'] == 'BAG':
                eje_sec = True
                linel = dict(color='rgb(150,150,150)', width=1, dash='dash')
            else:
                eje_sec = False
                linel = dict(width=2)
            fig3.add_trace(
                go.Scatter(
                    x=df_comp.index, 
                    y=(df_comp["close"]-base_level), 
                    line=linel,
                    mode="lines", 
                    connectgaps = True, 
                    name = symbol
                ),
                secondary_y=eje_sec
            )

    
    fig3.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
            dict(bounds=[21.1, 15], pattern="hour"),  # hide hours outside of 9.30am-4pm
            #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
        ]
    )

    fig3.update_layout(showlegend=True, 
                       xaxis_rangeslider_visible=False, 
                       title_text='Componentes', 
                       title_x = 0.5,
                       title_xanchor = 'center',
                       margin=dict(l=10, r=10, t=40, b=40),
                       legend_x=0, legend_y=1,
                    )

    return fig3

def insideDetailsStrategia (estrategia, graphColumn1, graphColumn2, graphComponentes):
    stratType = estrategia['type']
    collapseDetails = None
    if stratType == 'PentagramaRu':
        collapseDetails = webFE.webFENew_Strat_PentaRu.insideDetailsPentagramaRu (estrategia, graphColumn1, graphColumn2, graphComponentes)
    
    return collapseDetails


def layout_getStrategyHeader (estrategia, update = False):

    if estrategia == None:
        return no_update
    
    symbol = estrategia['symbol']
    strategyType = estrategia['type']
    posQty = estrategia['classObject'].currentPos_
    stratEnabled = estrategia['classObject'].stratEnabled_
    contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
    if not contrato:
        logging.error ('Error cargando estrategia Headerde %s. No tenemos el contrato cargado en RT_Data', symbol)
        return no_update
    
    if update == True:
        # contrato['dbPandas'].toPrint Es el precio del contrato
        # contrato['dbPandas'].toPrintPnL Es el PnL del contrato
        # estrategia['classObject'].pandas_.toPrint Es el numero de Execs
        if contrato['dbPandas'] == None:
            return no_update
        if contrato['dbPandas'].toPrint == False and contrato['dbPandas'].toPrintPnL == False and estrategia['classObject'].pandas_.toPrint == False:
            logging.debug ('Header estrategia no actualizado. No hay datos nuevos')
            return no_update

    dailyPnL = ''
    realizedPnL = ''
    unrealizedPnL = ''
    totalPnl = ''
    priceBuy = ''
    priceSell = ''
    priceLast = ''
    priceTotal = ''

    if contrato != None:
        lastPnL = contrato['dbPandas'].dbGetLastPnL()
        if lastPnL['dailyPnL'] != None:
            dailyPnL = formatCurrency(lastPnL['dailyPnL'])
        if lastPnL['realizedPnL'] != None:
            realizedPnL = formatCurrency(lastPnL['realizedPnL'])
        if lastPnL['unrealizedPnL'] != None:
            unrealizedPnL = formatCurrency(lastPnL['unrealizedPnL'])
        totalPnl = dailyPnL + '/' + realizedPnL + '/' + unrealizedPnL
        
        priceBuy = formatCurrency(contrato['currentPrices']['BUY'])
        priceSell = formatCurrency(contrato['currentPrices']['SELL'])
        priceLast = formatCurrency(contrato['currentPrices']['LAST'])
        priceTotal = priceBuy + '/' + priceSell + '/' + priceLast

    execToday = 'Na'
    execTotal = 'Na'
    #if strategyType == 'Pentagrama':
    execToday = estrategia['classObject'].pandas_.dbGetExecCountToday()
    execTotal = estrategia['classObject'].pandas_.dbGetExecCountAll()
    estrategia['classObject'].pandas_.toPrint = False
    execString = str(execToday) + '/' + str(execTotal)

    # Cabecera para cada contrato con estrategia

    color_switch = 'bg-danger'
    if stratEnabled:
        color_switch = 'bg-success'
    
    headerRow = dbc.Row(
        [
            dbc.Col(dbc.Button(symbol,id={'role': 'boton_strategy_header', 'strategy':strategyType, 'symbol': symbol}), class_name = 'bg-primary mr-1', width = 3),
            dbc.Col(html.Div(posQty), class_name = 'bg-primary mr-1', width = 1),
            dbc.Col(html.Div(priceTotal), class_name = 'bg-primary mr-1', width = 2),
            dbc.Col(html.Div(totalPnl), class_name = 'bg-primary mr-1', width = 3),
            dbc.Col(html.Div(execString), class_name = 'bg-primary mr-1', width = 2),
            dbc.Col(dbc.Switch(id={'role': 'switchStratEnabled', 'strategy':strategyType, 'symbol': symbol}, input_class_name = color_switch, value = stratEnabled), class_name = 'bg-primary mr-1', width = 1),
        ], className = 'text-white mb-1'
    )
    
    contrato['dbPandas'].toPrintPnL = False
    contrato['dbPandas'].toPrint = False
    
    return headerRow

def modal_addStrategy():

    # Aquí habria que añadir un id para el tipo de estrategia, y con un callback decidir el responseBody

    Symbol = dcc.Input(
        id = "strategy_create_symbol",
        type = "text",
        placeholder = "",
    )

    Qty = dcc.Input(
        id = "strategy_create_qty",
        type = "number",
        placeholder = "0",
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
        options = [250, 300, 350], 
        value = 250, 
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


    responseBody = html.Div([
        html.P('Simbolo Estrategia: ',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        Symbol,
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
    ])
    
    modal = html.Div(
        [
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Crear Ordem", id = "modalStrategyCreateHeader")),
                    dbc.ModalBody(responseBody, id = "modalStrategyCreateBody"),
                    dbc.ModalFooter([
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
            ),
        ]
    )
    return modal
'''
# Callback para general una orden en el contrato
@callback(
    Output("contract_orders_create_symbol", "placeholder"),
    Output("modalContratoOrdenCreate_main", "is_open"),
    Input({'role': 'boton_order_create', 'gConId': ALL}, "n_clicks"),
    Input("contract_orders_create_symbol", "placeholder"),
    Input("contract_orders_create_qty", "value"),
    Input("contract_orders_create_LmtPrice", "value"),
    Input("contract_orders_create_action", "value"),
    Input("contract_orders_create_orderType", "value"),
    Input("modalContratoOrdenCreate_boton_create", "n_clicks"),
    Input("modalContratoOrdenCreate_boton_close", "n_clicks"),
    State("modalContratoOrdenCreate_main", "is_open"), prevent_initial_call = True,
)
def createStrategy (n_button_open, s_symbol,  n_qty, n_LmtPrice, s_action, s_orderType, n_button_create, n_button_close, open_status):

    # Esto es por si las moscas
    if not ctx.triggered_id:
        raise PreventUpdate
'''
# Callback para enable/disable estrategia
@callback(
    Output({'role': 'switchStratEnabled', 'strategy':MATCH, 'symbol': MATCH}, "input_class_name"),
    Input({'role': 'switchStratEnabled', 'strategy':MATCH, 'symbol': MATCH}, "value"), 
    prevent_initial_call = True,
)
def switchStrategy(state):
    
    if not ctx.triggered_id:
        return no_update
    symbol = str(ctx.triggered_id.symbol)
    strategyType = ctx.triggered_id['strategy']

    if state:
        logging.info ('Estrategia [%s] del tipo: %s Enabled', symbol, strategyType)
        ret = 'bg-success'
    else:
        logging.info ('Estrategia [%s] del tipo: %s Disabled', symbol, strategyType)
        ret = 'bg-danger'

    globales.G_RTlocalData_.strategies_.strategyEnableDisable (symbol, strategyType, state)
    
    return ret

# Callback para colapsar o mostrar filas Strategias
@callback(
    Output({'role': 'colapse_strategy', 'strategy':MATCH, 'symbol': MATCH}, "is_open"),
    Input({'role': 'boton_strategy_header', 'strategy':MATCH, 'symbol': MATCH}, "n_clicks"),
    State({'role': 'colapse_strategy', 'strategy':MATCH, 'symbol': MATCH}, "is_open"),
    prevent_initial_call = True,
)
def toggle_colapse_strategy(n_button, is_open):
    if n_button:
        return not is_open
    return is_open

#Callback para actualizar fila de valores de Strategies
@callback(
    Output({'role':'estrategia_header', 'strategy':MATCH, 'symbol': MATCH}, "children"),
    Input({'role': 'IntervalHeaderStrategy', 'strategy':MATCH, 'symbol': MATCH}, 'n_intervals'),
    prevent_initial_call = True,
)
def actualizarFilaStrategies (n_intervals):
    if not ctx.triggered_id:
        raise PreventUpdate
    if globales.G_RTlocalData_.strategies_ == None:
        raise PreventUpdate
    logging.debug ('Actualizando Estrategia Fila')
    symbol = ctx.triggered_id['symbol']
    strategyType = ctx.triggered_id['strategy']

    estrategia = globales.G_RTlocalData_.strategies_.strategyGetStrategyBySymbolAndType (symbol, strategyType)

    resp = layout_getStrategyHeader (estrategia, True)
    return resp

#Callback para recargar todas las estrategias desde fichero
@callback(
    Output("modal_reloadStrategiesOK", "children"),
    Output("modal_reloadStrategiesOK_Body", "children"),
    Output("modal_reloadStrategiesOK_main", "is_open"),
    Input({'role': 'ZoneButtonReloadAll'}, "n_clicks"),
    Input("modal_reloadStrategiesOK_boton_close", "n_clicks"),
    State("modal_reloadStrategiesOK_main", "is_open"), prevent_initial_call = True,
)
def reloadStrats (n_button_open, n_button_close, open_status):

    # Esto es por si las moscas
    logging.debug('%s',n_button_open )
    logging.debug('%s',ctx.triggered_id )
    responseHeader = ''
    responseBody = ''

    if n_button_open == 0:
        raise PreventUpdate

    if ctx.triggered_id == "modal_reloadStrategiesOK_boton_close":
        return responseHeader, responseBody, False
    
    try:
        globales.G_RTlocalData_.strategies_.strategyInit ()
    except:
        responseHeader = 'Error'
        responseBody = 'Error al recargar estrategias'     
    else:
        responseHeader = 'Aceptado'
        responseBody = 'Todas las estrategias recargadas. Recarga el navegador'

    return responseHeader, responseBody, True

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
    stratType = ctx.triggered_id['strategy']
    estrategia = globales.G_RTlocalData_.strategies_.strategyGetStrategyBySymbolAndType (symbol, stratType)

    fig3 = layout_getFigura3(estrategia, state_base)

    #return  zonasFilaBorderDown, no_update, no_update
    return  fig3