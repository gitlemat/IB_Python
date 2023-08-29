from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
from dash.exceptions import PreventUpdate

import webFE.webFENew_Strat_Penta
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

        logging.debug ('Ya tengo la fig2')

        collapseDetails = insideDetailsStrategia (estrategia, graphColumn1, graphColumn2)

        # Lo añadimos a la pagina/tab:

        tabEstrategias.append(headerRow)
        tabEstrategias.append(collapseDetails)    

        logging.debug ('Ya tengo todo')    

    return tabEstrategias


def layout_getFigura1(estrategia):
    stratType = estrategia['type']
    fig1 = None
    if stratType == 'Pentagrama':
        fig1 = webFE.webFENew_Strat_Penta.layout_getFigureHistoricoPen (estrategia)
    if stratType == 'PentagramaRu':
        fig1 = webFE.webFENew_Strat_PentaRu.layout_getFigureHistoricoPenRu (estrategia)

    return fig1


def layout_getFigura2(estrategia):
    stratType = estrategia['type']
    fig2 = None
    if stratType == 'Pentagrama':
        fig2 = webFE.webFENew_Strat_Penta.layout_getFigureTodayPen (estrategia)
    if stratType == 'PentagramaRu':
        fig2 = webFE.webFENew_Strat_PentaRu.layout_getFigureTodayPenRu (estrategia)

    return fig2

def insideDetailsStrategia (estrategia, graphColumn1, graphColumn2):
    stratType = estrategia['type']
    collapseDetails = None
    if stratType == 'Pentagrama':
        collapseDetails = webFE.webFENew_Strat_Penta.insideDetailsPentagrama (estrategia, graphColumn1, graphColumn2)
    if stratType == 'PentagramaRu':
        collapseDetails = webFE.webFENew_Strat_PentaRu.insideDetailsPentagramaRu (estrategia, graphColumn1, graphColumn2)
    
    return collapseDetails


def layout_getStrategyHeader (estrategia, update = False):
    
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
    
    headerRow = dbc.Row(
        [
            dbc.Col(dbc.Button(symbol,id={'role': 'boton_strategy_header', 'strategy':strategyType, 'symbol': symbol}), className = 'bg-primary mr-1', width = 3),
            dbc.Col(html.Div(posQty), className = 'bg-primary mr-1', width = 1),
            dbc.Col(html.Div(priceTotal), className = 'bg-primary mr-1', width = 2),
            dbc.Col(html.Div(totalPnl), className = 'bg-primary mr-1', width = 3),
            dbc.Col(html.Div(execString), className = 'bg-primary mr-1', width = 2),
            dbc.Col(dbc.Switch(id={'role': 'switchStratEnabled', 'strategy':strategyType, 'symbol': symbol}, value = stratEnabled), className = 'bg-primary mr-1', width = 1),
        ], className = 'text-white mb-1'
    )
    
    contrato['dbPandas'].toPrintPnL = False
    contrato['dbPandas'].toPrint = False
    
    return headerRow


# Callback para enable/disable estrategia
@callback(
    Output({'role': 'switchStratEnabled', 'strategy':MATCH, 'symbol': MATCH}, "value"),   # Dash obliga a poner un output.
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
    else:
        logging.info ('Estrategia [%s] del tipo: %s Disabled', symbol, strategyType)

    globales.G_RTlocalData_.strategies_.strategyEnableDisable (symbol, strategyType, state)
    
    return no_update

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