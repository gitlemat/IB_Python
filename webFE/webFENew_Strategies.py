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

    tabEstrategias = [
            dbc.Row(
                [
                    html.P("Lista de Estrategias", className='text-left text-secondary mb-4 display-6'),
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
                    dbc.Col(html.Div("Exec (Hoy/Total)"), className = 'bg-primary', width = 3),
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

        # Los dos graficos
        fig1 = layout_getFigura1(estrategia)   # Lo tengo en una funcion para que sea facil actualizar
        graphColumn1 = html.Div(
            dcc.Graph(
                    id={'role': 'graphDetailsComp', 'strategy': stratType, 'symbol': symbol},
                    animate = False,
                    figure = fig1
            )
        )
        
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

        collapseDetails = insideDetailsStrategia (estrategia, graphColumn1, graphColumn2)

        # Lo añadimos a la pagina/tab:

        tabEstrategias.append(headerRow)
        tabEstrategias.append(collapseDetails)        

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
        if contrato['dbPandas'].toPrintPnL == False and estrategia['classObject'].pandas_.toPrint == False:
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

    execToday = 'Na'
    execTotal = 'Na'
    if strategyType == 'Pentagrama':
        execToday = estrategia['classObject'].pandas_.dbGetExecCountToday()
        execTotal = estrategia['classObject'].pandas_.dbGetExecCountAll()
        estrategia['classObject'].pandas_.toPrint = False
    execString = str(execToday) + '/' + str(execTotal)

    # Cabecera para cada contrato con estrategia
    
    headerRow = dbc.Row(
        [
            dbc.Col(dbc.Button(symbol,id={'role': 'boton_strategy_header', 'strategy':strategyType, 'symbol': symbol}), className = 'bg-primary mr-1', width = 4),
            dbc.Col(html.Div(posQty), className = 'bg-primary mr-1', width = 1),
            dbc.Col(html.Div(dailyPnL), className = 'bg-primary mr-1', width = 1),
            dbc.Col(html.Div(realizedPnL), className = 'bg-primary mr-1', width = 1),
            dbc.Col(html.Div(unrealizedPnL), className = 'bg-primary mr-1', width = 1),
            dbc.Col(html.Div(execString), className = 'bg-primary mr-1', width = 3),
            dbc.Col(dbc.Switch(id={'role': 'switchStratEnabled', 'strategy':strategyType, 'symbol': symbol}, value = stratEnabled), className = 'bg-primary mr-1', width = 1),
        ], className = 'text-white mb-1'
    )
    
    contrato['dbPandas'].toPrintPnL = False
    
    return headerRow


# Callback para enable/disable estrategia
@callback(
    Output({'role': 'switchStratEnabled', 'strategy':MATCH, 'symbol': MATCH}, "value"),   # Dash obliga a poner un output.
    Input({'role': 'switchStratEnabled', 'strategy':MATCH, 'symbol': MATCH}, "value"), 
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
    strategyType = ctx.triggered_id['strategy']

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