from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import webFE.webFENew_Strat_PentaRu
from webFE.webFENew_Utils import formatCurrency, layout_getFigura_split
import globales
import logging
import random

logger = logging.getLogger(__name__)

def layout_strategies_tab():

    #strategyPentagrama_ = globales.G_RTlocalData_.strategies_.strategyPentagramaObj_.strategyPentagramaGetAll()
    #strategyPentagramaRu_ = globales.G_RTlocalData_.strategies_.strategyPentagramaRuObj_.strategyPentagramaRuGetAll()
    if globales.G_RTlocalData_ == None:
        return None
    if globales.G_RTlocalData_.strategies_ == None:
        return None
    
    strategyList = globales.G_RTlocalData_.strategies_.strategyGetAll()

    #{'symbol': symbol, 'type': type, 'classObject': classObject}

    #itemZG = 0 # Sirve para dar identidades unicas a las zonas
    ContentItems = []
    ####################################
    # Preparacion de Tab de Estratgias

    # Cabecera

    logging.debug ('Empiezo a calcular tab')

    botonCreateStrat1 = webFE.webFENew_Strat_PentaRu.createStratBoton()

    breload_text = html.Div('Recargar Todas', className="text9-7 d-inline-block")
    breload_icon = html.I(className="bi bi-file-earmark-arrow-up me-2 d-inline-block")
    breload_content = html.Span([breload_icon, breload_text])
    boton_reload = dbc.Button(breload_content, id={'role': 'ZoneButtonReloadAll'}, className="text9-7 d-inline-block me-0", n_clicks=0)
    boton_reload_tip = dbc.Tooltip("Recargar todas las estrategias desde el fichero", target={'role': 'ZoneButtonReloadAll'})
    
    bcrear_text = html.Div('Crear Strategias', className="text9-7 d-inline-block")
    bcrear_icon = html.I(className="bi bi-plus-square me-2 d-inline-block")
    bcrear_content = html.Span([bcrear_icon, bcrear_text])
    boton_crear = dbc.Button(bcrear_content, id={'role': 'strategy_add_new_general'}, className="text9-7 d-inline-block me-0", n_clicks=0)
    boton_crear_tip = dbc.Tooltip("Abrir menu para crear nuevas estrategias", target={'role': 'strategy_add_new_general'})
    
    botonesStrategyTopButtons = html.Div(
        [
            boton_reload,
            boton_reload_tip,
            boton_crear,
            boton_crear_tip
        ],
        className="d-grid gap-2 d-flex",
    )

    caja_add_strategies_contenido = html.Div(
        [
            botonCreateStrat1,
        ],
        className="d-grid gap-2 d-flex",
    )

    caja_add_strategies = dbc.Collapse(
        dbc.Row(
            dbc.Col(
                dbc.Card(caja_add_strategies_contenido, body=True)
            ),
        ),
        id={'role': 'colapse_strategy_add_general'},
        is_open=False,
        className = 'mb-3',
    )
    
    tabEstrategias = [
        dbc.Row(
            [

                dbc.Col(
                    html.P("Estrategias", className='text-left mb-0 text-secondary display-6'),
                    className = 'ps-0',
                    width = 7
                ),
            ],
            className = 'mb-3',
        ),
        dbc.Row(
            [
                botonesStrategyTopButtons
            ],
            className = 'mb-3',
        ),
        caja_add_strategies,
        dbc.Row(
            [
                html.Hr()
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.Div("Symbol"), id='strat-header-symbol', className = 'text9-7 bg-primary mr-1', xs=5, md=3), # xs-5 md-3
                dbc.Col(html.Div("Pos"), id='strat-header-pos', className = 'text9-7 bg-primary mr-1', xs=1, md=1),    # xs-1 
                dbc.Col(html.Div("AvgCost"), id='strat-header-bsl', className = 'text9-7 bg-primary mr-1', xs=2, md=1), # md-2 d-none d-md-block
                dbc.Col(html.Div("Last"), id='strat-header-bsl', className = 'text9-7 bg-primary mr-1', xs=2, md=1), # md-2 d-none d-md-block
                dbc.Col(html.Div("PnL Estrategia"), id='strat-header-pnl', className = 'text9-7 d-none d-md-block bg-primary mr-1', md=3), # md-3 d-none d-md-block
                dbc.Col(html.Div("Exec (Hoy/Total)"), className = 'text9-7 d-none d-md-block bg-primary', md=2), # md-2 d-none d-md-block
                dbc.Col(html.Div("Enabled"), id='strat-header-en', className = 'text9-7 md-1 bg-primary', xs=2, md=1), # xs-2
            ], className = 'mb-3 text-white', id='text9-7 strat-header'
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
                    headerRowInn, id ={'role':'estrategia_header', 'strategy': stratType, 'symbol': symbol}, className="text9-7"
                ),
                dcc.Interval(
                    id={'role': 'IntervalHeaderStrategy', 'strategy': stratType, 'symbol': symbol},
                    interval= random_wait, # in milliseconds
                    n_intervals=0
                )
            ]
        )

        logging.debug ('Ya tengo la cabecera')

        collapseDetails = insideDetailsStrategia (estrategia)

        # Lo añadimos a la pagina/tab:

        tabEstrategias.append(headerRow)
        tabEstrategias.append(collapseDetails)    
        #tabEstrategias.append(modal_contratoOrdenCreate())

    # Por ultimo los modals
    modals = modalsStrategia()
    tabEstrategias.append(html.Div(modals))

    logging.debug ('Ya tengo todo')    

    return tabEstrategias

def modalsStrategia ():   # Igual esto se puede quitar si añadimos los modals a insideDetailsStrategia
    modals = []
    modals += webFE.webFENew_Strat_PentaRu.insideModalsPentagramaRu ()
    
    return modals

def insideDetailsStrategia (estrategia):
    stratType = estrategia['type']
    collapseDetails = None
    if stratType == 'PentagramaRu':
        collapseDetails = webFE.webFENew_Strat_PentaRu.insideDetailsPentagramaRu (estrategia)
    
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

    AvgPrice = estrategia['classObject'].strategyGetExecPnL()['avgPrice']
    AvgPriceFmt = formatCurrency(AvgPrice)
    todayPnl = formatCurrency(estrategia['classObject'].strategyGetExecPnL()['PnL'])
    unrealNum = estrategia['classObject'].strategyGetExecPnLUnrealized()
    unrealNumFmt = formatCurrency(unrealNum)

    totalPnl = todayPnl+'/'+unrealNumFmt

    priceLast = ''
    if contrato != None:
        priceLast = formatCurrency(contrato['currentPrices']['LAST'])

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
            dbc.Col(html.Button(symbol,id={'role': 'boton_strategy_header', 'strategy':strategyType, 'symbol': symbol}), class_name = 'text9-7 bg-primary mr-1', xs=5, md=3),
            dbc.Col(html.Div(posQty), class_name = 'bg-primary mr-1', xs=1, md=1),
            dbc.Col(html.Div(AvgPriceFmt), class_name = 'bg-primary mr-1', xs=2, md=1),
            dbc.Col(html.Div(priceLast), class_name = 'bg-primary mr-1', xs=2, md=1),
            dbc.Col(html.Div(totalPnl), class_name = 'd-none d-md-block bg-primary mr-1', md=3),
            dbc.Col(html.Div(execString), class_name = 'd-none d-md-block bg-primary mr-1', md=2),
            dbc.Col(dbc.Switch(id={'role': 'switchStratEnabled', 'strategy':strategyType, 'symbol': symbol}, input_class_name = color_switch, value = stratEnabled), class_name = 'bg-primary mr-1', xs=2, md=1),
        ], className = 'text-white mb-1'
    )
    
    contrato['dbPandas'].toPrintPnL = False
    contrato['dbPandas'].toPrint = False
    
    return headerRow


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

# Callback para colapsar o mostrar crear Strategias
@callback(
    Output({'role': 'colapse_strategy_add_general'}, "is_open"),
    Input({'role': 'strategy_add_new_general'}, "n_clicks"),
    State({'role': 'colapse_strategy_add_general'}, "is_open"),
    prevent_initial_call = True,
)
def toggle_colapse_strategy_add(n_button, is_open):
    if n_button:
        return not is_open
    return is_open