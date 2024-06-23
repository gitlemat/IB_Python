from dash import html
from dash import dcc
from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
from dash.exceptions import PreventUpdate

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from webFE.webFENew_Utils import formatCurrency, layout_getFigureHistorico, layout_getFigura_split
import random
import globales
import logging

logger = logging.getLogger(__name__)


#####################################################################################################################
#####################################################################################################################
## Contratos

def layout_contratos_tab ():

    data = globales.G_RTlocalData_.contratoReturnDictAll()
    ContentItems = []
    
    #################################
    # Ahora creamos el tab de contratos usando la info anterior
    tabContratos = [
            dbc.Row(
                [
                    html.P("Lista de Contratos", className='text-left text-secondary mb-4 ps-0 display-6'),
                    html.Hr()
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(html.Div("Symbol"), id='contract-header-symbol', className = 'text9-7 bg-primary mr-1', xs=5, md = 3),
                    dbc.Col(html.Div("Pos"), id='contract-header-pos', className = 'text9-7 bg-primary mr-1', xs=1, md=1),
                    dbc.Col(html.Div("AvgPrice"), id='contract-header-avg', className = 'text9-7 bg-primary', xs=2, md=1),
                    dbc.Col(html.Div("Last"), id='contract-header-last', className = 'text9-7 bg-primary',  xs=2, md=1),
                    dbc.Col(html.Div("PnL (daily/real/unreal)"), id='contract-header-comm', className = 'text9-7 d-none d-md-block bg-primary', md = 4),
                    dbc.Col(html.Div("Order"), id='contract-header-order', className = 'text9-7 bg-primary',  xs=2, md=2),
                ], className = 'mb-3 text-white'
                ),
            ]


    #################################
    # Preparacion de Tab de contratos
    tabContratos_ind = []
    tabContratos_dir = []
    for gConId, contrato in data.items():

        indirect = globales.G_RTlocalData_.contractIndirectoGet (gConId) # Podria leer de contrato, pero es una guarregria (como mucho de lo que hay aqui)
        logging.debug ('Contrato Indirecto %s', indirect)
        
        headerRowInn = contratosObtenerFilas (contrato, False)  
        random_wait = random.randint(0,2000) + 4000

        headerRow = html.Div(
            [
                html.Div(
                    headerRowInn, className = 'text9-7', id ={'role':'contract_header', 'gConId': str(gConId)}
                ),
                dcc.Interval(
                    id={'role': 'IntervalContractLine', 'gConId': str(gConId)},
                    interval= random_wait, # in milliseconds
                    n_intervals=0
                )
            ]
        )

        ret = contratosObtenerInsideDetails (contrato, data, False)

        insideDetailsData = ret['caja']
        graphColumn = ret['graphOhcl']
        graphSplit = ret['graphSplit']
        #insideDetailsBotonesZonas.append(dbc.Row())

        
        bSaveEn = not contrato['dbPandas'].toSaveComp
        buttonExpandYFinance = dbc.Button("yFinance", id={'role': 'yFinanceButton', 'gConId':str(gConId)}, className="text9-7 me-2", n_clicks=0)
        buttonSaveYFinance = dbc.Button("Guardar", id={'role': 'yFinanceSaveButton', 'gConId':str(gConId)}, className="text9-7 me-2", n_clicks=0, disabled=bSaveEn)
        buttonRefresh = dbc.Button("Refresh", id={'role': 'RefreshButton', 'gConId':str(gConId)}, className="text9-7 me-2", n_clicks=0)
        
        # Todo lo que se oculta junto
        collapseDetails = dbc.Collapse(
            [
                dbc.Row(
                    [
                        dbc.Col(insideDetailsData, className = 'noPads', xs=12, md=5),
                        dbc.Col(
                            [
                                dbc.Row(graphColumn),
                                dbc.Row(
                                    [
                                        dbc.Col(buttonExpandYFinance),
                                        dbc.Col(buttonSaveYFinance),
                                        dbc.Col(buttonRefresh),
                                    ],
                                ),
                            ], xs=12, md=7)
                    ],
                ),
                dbc.Row(
                    graphSplit
                )
            ],
            className = 'text9-7 mb-2',
            id={'role': 'colapseContract', 'gConId': str(gConId)},
            is_open=False,
        )        

        if indirect:
            tabContratos_ind.append(headerRow)
            tabContratos_ind.append(collapseDetails)
        else:
            tabContratos_dir.append(headerRow)
            tabContratos_dir.append(collapseDetails)

    # Añadimos los directos e indirectos
    tabContratos += tabContratos_dir
    tabContratos.append(html.Hr())
    tabContratos += tabContratos_ind

    tabContratosWLLabel = [
        dbc.Row(
            [
                html.Hr(className='mt-4'),
                html.P("Contratos WatchList", className='text-left text-secondary mb-4 ps-0 display-6')
            ]
        ),
        dbc.Row(
            [
                contratosEditWatchList(),
            ],
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Button("Guardar", id={'role': 'ContractWLButtonSave'}, className="text9-7 mr-3, mt-4", n_clicks=0),
                        dbc.Button("Reload", id={'role': 'ContractWLButtonReload'}, className="text9-7 mr-3, mt-4", n_clicks=0)
                    ],
                    className = 'noPads',
                    xs = 12, md = 3,
                ),
            ]
        ),
    ]

    tabContratos += tabContratosWLLabel   
    tabContratos.append(modal_contratoOrdenCreate())
    tabContratos.append(modal_contratoUpdateWathchList())
    return tabContratos

def contratosObtenerFilas (contrato, update = False):
    gConId = contrato['gConId']
    posicion = contrato['pos']
        
    insideDetailsData = []
    if posicion == None:
        posQty = 0
        posavgCost = 0
    else:
        posQty = posicion 
        posavgCost = formatCurrency(contrato['posAvgPrice'])
    priceLast = formatCurrency(contrato['currentPrices']['LAST'])
    
    dailyPnL = '$-.-'
    realizedPnL = '$-.-'
    unrealizedPnL = '$-.-'
    totalPnl = ''
    lastPnL = contrato['dbPandas'].dbGetLastPnL()
    if lastPnL['dailyPnL'] != None:
        dailyPnL = formatCurrency(lastPnL['dailyPnL'])
    if lastPnL['realizedPnL'] != None:
        realizedPnL = formatCurrency(lastPnL['realizedPnL'])
    if lastPnL['unrealizedPnL'] != None:
        unrealizedPnL = formatCurrency(lastPnL['unrealizedPnL'])
    totalPnl = dailyPnL + '/' + realizedPnL + '/' + unrealizedPnL

    symbol = contrato['fullSymbol']
    # Cada fila de cabecera
    headerRow = dbc.Row(
            [
                dbc.Col(html.Button(symbol,className = 'botonContract', id={'role': 'botonContract', 'gConId': str(gConId)}), className = 'text9-7 bg-primary mr-1', xs=5, md=3),
                dbc.Col(html.Div(posQty), className = 'text9-7 bg-primary mr-1', xs=1, md=1),
                dbc.Col(html.Div(posavgCost), className = 'text9-7 bg-primary', xs=2, md=1),
                dbc.Col(html.Div(priceLast), className = 'text9-7 bg-primary', xs=2, md=1),
                dbc.Col(html.Div(totalPnl), className = 'text9-7 d-none d-md-block bg-primary', md=4),
                dbc.Col(html.Button(html.I(className="bi bi-bag-plus me-2"),className = 'botonContract', id={'role': 'boton_order_create', 'gConId': str(gConId)}), className = 'text9-7 bg-primary',  xs=2, md=2),
            ], className = 'text-white mb-1',
    )  

    return headerRow

def contratosObtenerInsideDetails (contrato, data, update = False):
    # Los detalles que se ocultan. Dos columnas, detalles y figura 
    # Primero los detalles
    gConId = contrato['gConId']
    symbol = contrato['fullSymbol']
    insideDetailsData = []
    insideDetailsData.append(html.Div(children = "gConId: " + str(contrato['gConId'])))
    insideDetailsData.append(html.Div(children = "ConId: " + str(contrato['contract'].conId)))
    insideDetailsData.append(html.Div(children = "Local symbol: " + str(contrato['contract'].localSymbol)))
    insideDetailsData.append(html.Div(children = "secType: " + str(contrato['contract'].secType)))
    insideDetailsData.append(html.Div(children = "indirecto: " + str(contrato['contratoIndirecto'])))
    if contrato['contract'].secType == "BAG":
        for leg in contrato['contract'].comboLegs:
            insideDetailsData.append(html.Div(children = "Leg: "))
            insideDetailsData.append(html.Div(children = "ConId: " + str(leg.conId), style = {"margin-left": "40px"}))
            insideDetailsData.append(html.Div(children = "Action: " + str(leg.action), style = {"margin-left": "40px"}))
            insideDetailsData.append(html.Div(children = "Ratio: " + str(leg.ratio), style = {"margin-left": "40px"}))
            insideDetailsData.append(html.Div(children = "LocalSymbol: " + data[leg.conId]['contract'].localSymbol, style = {"margin-left": "40px"}))
            insideDetailsData.append(html.Div(children = "LastOrderDate: " + data[leg.conId]['contract'].lastTradeDateOrContractMonth, style = {"margin-left": "40px"}))

    elif contrato['contract'].secType == "FUT":
        insideDetailsData.append(html.Div(children = "Date: " + str(contrato['contract'].lastTradeDateOrContractMonth)))

    contenido_caja = html.Div(
        dbc.Row(
                [
                    dbc.Col(insideDetailsData, width=12),

                ]
            ),
            className='text9-7'
        )

    caja_inicial_top = dbc.Card(contenido_caja, body=True),

    # El grafico
    #fig = px.line(contrato['dbPandas'].dbGetDataframe(), x="timestamp", y="LAST", title="LAST Evolution") 
    #fig.update_layout(xaxis = dict(type="category")) # Para que no deje los vacios de fecha de cierre

    fig = layout_getFigureHistorico(contrato)  # de Utils
    
                       
    graphColumn = html.Div(
        dcc.Graph(
                id={'role': 'graphDetails', 'gConId': str(gConId)},
                figure = fig 
        )
    )

    graphComponentes = []
    if not contrato['contratoIndirecto']:
        fig3 = layout_getFigura_split(symbol)   # Lo tengo en una funcion para que sea facil actualizar
        graphColumn3 = html.Div([
            dcc.Graph(
                    id={'role': 'graphDetailsSpread', 'symbol': symbol},
                    animate = False,
                    figure = fig3
            )
        ])
        switch_compon_base = html.Div([
            dbc.Switch(
                id={'role': 'switch_componentes_base', 'symbol': symbol},
                label="Inicio a cero",
                value=False,
                className = 'mt-0 mt-md-5' 
            )],
            id={'role': 'switch_componentes_form', 'symbol': symbol},
        )
    
        graphComponentes = [
            dbc.Col(graphColumn3, md=10),
            dbc.Col(switch_compon_base, md=2)
        ]

    ret = {'caja': caja_inicial_top, 'graphOhcl': graphColumn, 'graphSplit': graphComponentes}

    return ret

def contratosEditWatchList ():
    contractsWL = globales.G_RTlocalData_.contractReturnFixedWatchlist()
    text = ''
    for line in contractsWL:
        text += line + '\n'
    n_rows = len (contractsWL)
    
    textareas = html.Div(
        [
            dbc.Textarea(
                id = {'role': 'contratosInputWatchList'},
                rows = n_rows, 
                value = text.rstrip(), 
                className="text9-7 ps-0"
            ),
        ],
        className = 'noPads',
    )
    return textareas

def modal_contratoUpdateWathchList():
    modal = html.Div(
        [
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Actualizar Watch List", id = "modalContratoWatchListUpdateHeader")),
                    dbc.ModalBody("", id = "modalContratoWatchListUpdateBody"),
                    dbc.ModalFooter([
                        dbc.Button(
                            "Close", id="modalContratoWatchListUpdate_boton_close", className="ms-auto", n_clicks=0
                        )
                    ]),
                ],
                id="modalContratoWatchListUpdate_main",
                is_open=False,
            ),
        ]
    )
    return modal

def modal_contratoOrdenCreate():

    orderSymbol = dcc.Input(
        id = "contract_orders_create_symbol",
        type = "text",
        readOnly = True,
        placeholder = "",
    )

    orderQty = dcc.Input(
        id = "contract_orders_create_qty",
        type = "number",
        placeholder = "0",
    )

    orderLmtPrice = dcc.Input(
        id = "contract_orders_create_LmtPrice",
        type = "number",
        placeholder = "0",
    )

    orderAction = dcc.Dropdown(
        options = ['BUY', 'SELL'], 
        value = 'BUY', 
        id = 'contract_orders_create_action'
    )

    orderType = dcc.Dropdown(
        options = ['MKT', 'LMT', 'STP', 'MKTGTC', 'LMTGTC', 'STPGTC'], 
        value = 'MKT', 
        id='contract_orders_create_orderType'
    )

    orderSLType = dcc.Input(
        id = "contract_orders_create_orderTypeSL",
        type = "text",
        readOnly = True,
        placeholder = "STPGTC",
    )

    orderLmtPriceSL = dcc.Input(
        id = "contract_orders_create_LmtPriceSL",
        type = "number",
        placeholder = "0",
    )

    

    responseBody = html.Div([
        html.P('Contract Symbol: ',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderSymbol,
        html.P('Order Action:',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderAction,
        html.P('Order Type:',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderType,
        html.P('Order Qty:',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderQty,
        html.P('Order LMT Price:',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderLmtPrice,
        html.P('Crear OCA:',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        dbc.Switch(id={'role': 'contract_orders_create_OCA_ENABLE'}, value = False),
        dbc.Collapse(
            [
                html.P('OrderSL LMT Price:',
                    style={'margin-top': '8px', 'margin-bottom': '4px'},
                    className='font-weight-bold'),
                orderLmtPriceSL,
                html.P('OrderSL Type:',
                    style={'margin-top': '8px', 'margin-bottom': '4px'},
                    className='font-weight-bold'),
                orderSLType,
            ],
            id={'role': 'colapse_OCA'},
            is_open=False,
        )
    ])
    
    modal = html.Div(
        [
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Crear Orden", id = "modalContratoOrdenCreateHeader")),
                    dbc.ModalBody(responseBody, id = "modalContratoOrdenCreateBody"),
                    dbc.ModalFooter([
                        dbc.Button(
                            "Crear", id="modalContratoOrdenCreate_boton_create", className="ms-auto", n_clicks=0
                        ),
                        dbc.Button(
                            "Close", id="modalContratoOrdenCreate_boton_close", className="ms-auto", n_clicks=0
                        )
                    ]),
                ],
                id="modalContratoOrdenCreate_main",
                is_open=False,
            ),
        ]
    )
    return modal

# Callback para colapsar o mostrar filas Generico
@callback(
    Output({'role': 'colapseContract', 'gConId': MATCH}, "is_open"),
    Input({'role': 'botonContract', 'gConId': MATCH}, "n_clicks"),
    State({'role': 'colapseContract', 'gConId': MATCH}, "is_open"),
    prevent_initial_call = True,
)
def toggle_colapse_contract(n_button, is_open):
    if n_button:
        return not is_open
    return is_open

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

    Input("contract_orders_create_orderTypeSL", "value"),
    Input("contract_orders_create_LmtPriceSL", "value"),
    
    Input("modalContratoOrdenCreate_boton_create", "n_clicks"),
    Input("modalContratoOrdenCreate_boton_close", "n_clicks"),
    State("modalContratoOrdenCreate_main", "is_open"), 
    State({'role': 'colapse_OCA'}, "is_open"),
    prevent_initial_call = True,
)
def createOrder (n_button_open, s_symbol,  n_qty, n_LmtPrice, s_action, s_orderType, s_orderTypeSL, n_LmtPriceSL, n_button_create, n_button_close, open_status, oca_status):

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

    contractText = ''

    logging.info('Trigger %s', ctx.triggered_id)

    if ctx.triggered_id == "modalContratoOrdenCreate_boton_close":
        return contractText, False

    #return no_update, no_update, no_update

    if ctx.triggered_id == "modalContratoOrdenCreate_boton_create":
        contrato = globales.G_RTlocalData_.contractGetBySymbol (s_symbol)
        secType = contrato['contract'].secType
        error = False

        try:
            n_qty = int (n_qty)
        except:
            error = True
        
        if s_orderType in ['LMT', 'STP', 'LMTGTC', 'STPGTC']:
            try:
                n_LmtPrice = float (n_LmtPrice)
            except:
                error = True
        else:
            n_LmtPrice = 0
        
        if error == False:
            mesg = ""
            if oca_status:
                mesg += 'Vamos a crear una pareja de ordenes OCA con:\n'
                mesg += "  Symbol: %s\n" % (s_symbol)
                mesg += "  secType: %s\n" % (secType)
                mesg += "  Action: %s\n" % (s_action)
                mesg += "  Qty: %s\n" % (n_qty)
                mesg += "  Orden LMT:\n"
                mesg += "    Price: %s\n" % (n_LmtPrice)
                mesg += "    Type: %s\n" % (s_orderType)
                mesg += "  Orden STP:\n"
                mesg += "    Price: %s\n" % (n_LmtPriceSL)
                mesg += "    Type: %s\n" % (s_orderTypeSL)
                logging.info (mesg)
                if n_LmtPriceSL == None:
                    logging.error ("Error con el n_LmtPriceSL")
                    return contractText, False
                try:
                    result = globales.G_RTlocalData_.orderPlaceOCA (s_symbol, contrato['contract'], secType, s_action, s_action, n_qty, n_LmtPrice, n_LmtPriceSL)
                    result = True
                except:
                    logging.error ("Exception occurred", exc_info=True)
            else:
                mesg += 'Vamos a crear una orden con:\n'
                mesg += "  Symbol: %s\n" % (s_symbol)
                mesg += "  secType: %s\n" % (secType)
                mesg += "  Action: %s\n" % (s_action)
                mesg += "  Qty: %s\n" % (n_qty)
                mesg += "  Price: %s\n" % (n_LmtPrice)
                mesg += "  Type: %s\n" % (s_orderType)
                mesg += "  Orden STP:\n"
                logging.info (mesg)
                try:
                    result = globales.G_RTlocalData_.orderPlaceBrief (s_symbol, contrato['contract'], secType, s_action, s_orderType, n_LmtPrice, n_qty)
                    result = True
                except:
                    logging.error ("Exception occurred", exc_info=True)

            return contractText, False
        else:
            return no_update

    if 'gConId' in ctx.triggered_id:
        gConId = int(ctx.triggered_id['gConId'])
        contrato = globales.G_RTlocalData_.contractGetContractbyGconId (gConId)

        #ahora hay que borrarla
        logging.info('Queremos crear ordenes para gConId: %s', str(gConId))
    
    
        if contrato != None and 'fullSymbol' in contrato:
            contractText = contrato['fullSymbol']
    
        return contractText, True

    # Para todos los demas:
    return no_update

# Callback para enable/disable OCA en dialog
@callback(
    Output({'role': 'colapse_OCA'}, "is_open"),
    Input({'role': 'contract_orders_create_OCA_ENABLE'}, "value"), 
    State({'role': 'colapse_OCA'}, "is_open"),
    prevent_initial_call = True,
)
def toggle_colapse_OCA(n_button, is_open):
    if n_button:
        return not is_open
    return is_open

# Callback para guardar watchlist
@callback(
    Output("modalContratoWatchListUpdateBody", "children"), 
    Output("modalContratoWatchListUpdate_main", "is_open"),
    Input({'role': 'ContractWLButtonSave'}, "n_clicks"),
    Input({'role': 'contratosInputWatchList'}, "value"),
    prevent_initial_call = True,
)
def guardarContractWL(n_button, textWL):
        # Esto es por si las moscas
    if not ctx.triggered_id or n_button == None:
        raise PreventUpdate

    if ctx.triggered_id['role'] != 'ContractWLButtonSave':
        raise PreventUpdate

    logging.info ('Id: %s', ctx.triggered_id)
    contractList = textWL.rstrip().split('\n')
    logging.info ('Lista:\n %s', contractList)

    ret = globales.G_RTlocalData_.contractWriteFixedWatchlist(contractList)
    if ret:
        body = 'Actualizada Correctamente'
    else:
        body = 'Ha habido algun error. Mira los logs'

    return body, True

# Callback para recargar watchlist
@callback(
    Output({'role': 'contratosInputWatchList'}, "value"),
    Output({'role': 'contratosInputWatchList'}, "rows"),
    Input({'role': 'ContractWLButtonReload'}, "n_clicks"),
    prevent_initial_call = True,
)
def reloadContractWL(n_button):
        # Esto es por si las moscas
    if not ctx.triggered_id or n_button == None:
        raise PreventUpdate

    logging.info ('Id: %s', ctx.triggered_id)
    contractsWL = globales.G_RTlocalData_.contractReturnFixedWatchlist()
    text = ''
    for line in contractsWL:
        text += line + '\n'
    n_rows = len (contractsWL)

    return text, n_rows

# Callback para cargar Finance
@callback(
    Output({'role': 'yFinanceButton', 'gConId': MATCH}, "n_clicks"),
    Input({'role': 'yFinanceButton', 'gConId': MATCH}, "n_clicks"),
    prevent_initial_call = True,
)
def yFinanceExpand(n_button):
        # Esto es por si las moscas
    if not ctx.triggered_id or n_button == None:
        raise PreventUpdate

    logging.info ('Id: %s', ctx.triggered_id)

    eso = globales.G_RTlocalData_.contractYFinanceExpand(ctx.triggered_id['gConId'])

    return n_button


# Callback para refresh y grabar contrato
@callback(
    Output({'role': 'yFinanceSaveButton', 'gConId': MATCH}, "disabled"),
    Output({'role': 'graphDetails', 'gConId': MATCH}, "figure"),
    Input({'role': 'RefreshButton', 'gConId': MATCH}, "n_clicks"),
    Input({'role': 'yFinanceSaveButton', 'gConId': MATCH}, "n_clicks"),
    prevent_initial_call = True,
)
def contractRefreshSave(n_button1, n_button2):
        # Esto es por si las moscas
    if not ctx.triggered_id or (n_button1 == None and n_button2 == None):
        raise PreventUpdate

    logging.info ('Id: %s', ctx.triggered_id)
    contrato = globales.G_RTlocalData_.contractGetContractbyGconId (ctx.triggered_id['gConId'])

    if not contrato:
        raise PreventUpdate 
    
    if ctx.triggered_id['role'] == 'yFinanceSaveButton':
        eso = globales.G_RTlocalData_.contractCompDataSave(ctx.triggered_id['gConId'])
    
    fig = layout_getFigureHistorico(contrato)  # de Utils

    bSaveEn = not contrato['dbPandas'].toSaveComp

    return bSaveEn, fig

#Callback para actualizar grafica Split
@callback(
    Output({'role': 'graphDetailsSpread', 'symbol': MATCH}, 'figure'),
    Input ({'role': 'switch_componentes_base', 'symbol': MATCH}, 'value'),
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