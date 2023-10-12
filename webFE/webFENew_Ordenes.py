from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
from dash import html
from dash import dcc
from dash.exceptions import PreventUpdate

import dash_bootstrap_components as dbc
from webFE.webFENew_Utils import formatCurrency
import logging
import globales
import random

logger = logging.getLogger(__name__)

def layout_ordenes_tab ():
    data = globales.G_RTlocalData_.orderReturnListAll()

    #################################
    # Preparacion de Tab de ordenes

    tabOrdenes = [
            dbc.Row(
                [

                    dbc.Col(
                        html.P("Lista de Ordenes", className='text-left mb-0 text-secondary display-6'),
                        className = 'ps-0',
                        width = 9
                    ),
                    dbc.Col(
                        html.Div(
                            dbc.Button("Pedir Update", id={'role': 'ZoneButtonReqOrderUpdate'}, className="me-0", n_clicks=0),
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
                    dbc.Col(html.Div("OrdenId"), className = 'bg-primary mr-1', width = 1),
                    dbc.Col(html.Div("Symbol"), className = 'bg-primary mr-1', width = 2),
                    dbc.Col(html.Div("Action"), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("Status"), className = 'bg-success', width = 1),
                    dbc.Col(html.Div("Fill Status"), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("LastFill"), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("Estrategia"), className = 'bg-primary', width = 3),
                    dbc.Col(html.Div("Update"), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("Cancel"), className = 'bg-primary', width = 1),
                ], className = 'mb-3 text-white'
                ),
            ]

    for orden in data:
        
        random_wait = random.randint(0,2000) + 4000
        headerRowInn = ordenesObtenerFilas (orden, False)

        lOrderId = orden['order'].orderId
        
        headerRow = html.Div(
            [
                html.Div(
                    headerRowInn, id ={'role':'orden_header', 'orderId': str(lOrderId)}
                ),
                dcc.Interval(
                    id={'role': 'IntervalOrdersLine', 'orderId': str(lOrderId)},
                    interval= random_wait, # in milliseconds
                    n_intervals=0
                )
            ]
        )

        insideDetailsData = ordenesObtenerInsideDetails (orden, False)        

        collapseDetails = dbc.Collapse(
            dbc.Row(
                [
                    dbc.Col(insideDetailsData),
                ],
            ),
            id={'role': 'colapse', 'index': lOrderId},
            is_open=False,
            
        )

        # Lo añadimos a la pagina/tab:

        tabOrdenes.append(headerRow)
        tabOrdenes.append(collapseDetails)
        tabOrdenes.append(modal_ordenUpdate())
        tabOrdenes.append(modal_ordenCancel())

    return tabOrdenes

def ordenesObtenerFilas (orden, update = False):
    #orden = globales.G_RTlocalData_.orderGetByOrderId(lOrderId)
    if orden == None or 'toPrint' not in orden:
        logging.debug ('Ordenes aun sin cargae')
        return no_update
    if orden['toPrint'] == False and update == True:
        logging.debug ('Header ordenes no actualizado. No hay datos nuevos')
        return no_update
    lOrderId = orden['order'].orderId
    lAction = orden['order'].action
    lQty = orden['order'].totalQuantity
    lStatus = orden['params']['status'] if 'status' in orden['params'] else ''
    lFilled = orden['params']['filled'] if 'filled' in orden['params'] else ''
    lRemaining = orden['params']['remaining'] if 'remaining' in orden['params'] else ''
    lLastFillPrice = orden['params']['lastFillPrice'] if 'lastFillPrice' in orden['params'] else ''
    symbol = globales.G_RTlocalData_.contractSummaryBrief(orden['contractId'])
    lFillState = str(lQty) + '/' + str(lFilled) + '/' + str(lRemaining)

    strategy = globales.G_RTlocalData_.strategies_.strategyGetStrategyByOrderId (lOrderId)
    if strategy != None and 'strategy' in orden and orden['strategy'] != None:
        strategy['strategy'] = orden['strategy'].straType_
    if strategy == None:
        lStrategy = 'N/A'
    else:
        lStrategy = strategy['strategy'] + ' [' + strategy['symbol'] + ']'

    headerRow = dbc.Row(
            [
                dbc.Col(dbc.Button(str(lOrderId),id={'role': 'boton', 'index': lOrderId}), className = 'bg-primary mr-1', width = 1),
                dbc.Col(html.Div(symbol), className = 'bg-primary mr-1', width = 2),
                dbc.Col(html.Div(lAction), className = 'bg-primary', width = 1),
                dbc.Col(html.Div(lStatus), className = 'bg-success', width = 1),
                dbc.Col(html.Div(lFillState), className = 'bg-primary', width = 1),
                dbc.Col(html.Div(lLastFillPrice), className = 'bg-primary', width = 1),
                dbc.Col(html.Div(lStrategy), className = 'bg-primary', width = 3),
                dbc.Col(dbc.Button(html.I(className="bi bi-pencil-square me-2"),id={'role': 'boton_order_update', 'orderId': str(lOrderId)}), className = 'bg-primary', width = 1),
                dbc.Col(dbc.Button(html.I(className="bi bi-x-circle me-2"),id={'role': 'boton_order_cancel', 'orderId': str(lOrderId)}), className = 'bg-primary', width = 1),
            ], className = 'text-white mb-1'
    )  
    orden['toPrint'] = False
    return headerRow

def ordenesObtenerInsideDetails (orden, update = False):
    lorderType = orden['order'].orderType
    lPermId = str(orden['order'].permId)
    lgConId = str(orden['contractId'])
    lLmtPrice = orden['order'].lmtPrice
    if lorderType == 'STP':
        lLmtPrice = orden['order'].auxPrice
    lTif = orden['order'].tif
    lOca = orden['order'].ocaGroup

    lLmtPrice = formatCurrency (lLmtPrice)

    insideDetailsData = []
    insideDetailsData.append(html.Div(children = "gConId: " + lgConId, style = {"margin-left": "40px"}))
    insideDetailsData.append(html.Div(children = "PermId: " + lPermId, style = {"margin-left": "40px"}))
    insideDetailsData.append(html.Div(children = "Order Type: " + lorderType, style = {"margin-left": "40px"}))
    insideDetailsData.append(html.Div(children = "Limit Price: " + lLmtPrice, style = {"margin-left": "40px"}))
    insideDetailsData.append(html.Div(children = "Time in Force: " + lTif, style = {"margin-left": "40px"}))
    insideDetailsData.append(html.Div(children = "OCA Group: " + lOca, style = {"margin-left": "40px"}))

    return insideDetailsData

def modal_ordenCancel():

    orderOrderId = dcc.Input(
        id = "order_cancel_orderId",
        type = "text",
        readOnly = True,
        placeholder = "",
    )

    responseBody = html.Div([
        html.P('Cancelamos esta: ',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderOrderId,
    ])
    
    modal = html.Div(
        [
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Cancelar Orden", id = "modal_cancelOrder")),
                    dbc.ModalBody(responseBody, id = "OrdenCancelBody"),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Cancelar", id="modal_cancelOrder_boton_cancel", className="ms-auto", n_clicks=0
                            ),
                            dbc.Button(
                                "Close", id="modal_cancelOrder_boton_close", className="ms-auto", n_clicks=0
                            )
                        ]
                    ),
                ],
                id="modal_cancelOrder_main",
                is_open=False,
            ),
        ]
    )
    return modal

def modal_ordenUpdate():

    orderSymbol = dcc.Input(
        id = "order_update_symbol",
        type = "text",
        readOnly = True,
        placeholder = "",
    )

    orderOrderId = dcc.Input(
        id = "order_update_orderId",
        type = "text",
        readOnly = True,
        placeholder = "",
    )

    orderQty = dcc.Input(
        id = "order_update_qty",
        type = "number",
        placeholder = "0",
    )

    orderLmtPrice = dcc.Input(
        id = "order_update_LmtPrice",
        type = "number",
        placeholder = "0",
    )

    orderAction = dcc.Input(
        type = "text",
        readOnly = True,
        id = 'order_update_action'
    )

    orderType = dcc.Input(
        type = "text",
        readOnly = True,
        id='order_update_orderType'
    )

    orderOCAID = dcc.Input(
        id = "order_update_OCAID",
        type = "number",
        readOnly = True,
        placeholder = "0",
    )

    orderParentId = dcc.Input(
        id = "order_update_parentId",
        type = "number",
        readOnly = True,
        placeholder = "0",
    )

    responseBody = html.Div([
        html.P('Contract Symbol: ',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderSymbol,
        html.P('OrderId: ',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderOrderId,
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
        html.P('OCA Name:',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderOCAID,
        html.P('Parent OrderId:',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderParentId,
    ])
    
    modal = html.Div(
        [
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Actualizar Orden", id = "OrdenUpdateHeader")),
                    dbc.ModalBody(responseBody, id = "OrdenUpdateBody"),
                    dbc.ModalFooter([
                        dbc.Button(
                            "Actualizar", id="modalOrdenUpdate_boton_update", className="ms-auto", n_clicks=0
                        ),
                        dbc.Button(
                            "Close", id="modalOrdenUpdate_boton_close", className="ms-auto", n_clicks=0
                        )
                    ]),
                ],
                id="modalOrdenUpdate_main",
                is_open=False,
            ),
        ]
    )
    return modal

# Callback para actualizar una orden en el contrato
@callback(
    Output("order_update_symbol", "placeholder"),
    Output("order_update_orderId", "value"),
    Output("order_update_qty", "value"),
    Output("order_update_LmtPrice", "value"),
    Output("order_update_action", "value"),
    Output("order_update_orderType", "value"),
    Output("order_update_OCAID", "value"),
    Output("order_update_parentId", "value"),
    Output("modalOrdenUpdate_main", "is_open"),
    Input({'role': 'boton_order_update', 'orderId': ALL}, "n_clicks"),
    Input("order_update_symbol", "placeholder"),
    Input("order_update_orderId", "value"),
    Input("order_update_qty", "value"),
    Input("order_update_LmtPrice", "value"),
    Input("order_update_action", "value"),
    Input("order_update_orderType", "value"),
    Input("order_update_OCAID", "value"),
    Input("order_update_parentId", "value"),
    Input("modalOrdenUpdate_boton_update", "n_clicks"),
    Input("modalOrdenUpdate_boton_close", "n_clicks"),
    State("modalOrdenUpdate_main", "is_open"), prevent_initial_call = True,
)
def updateOrder (n_button_open, s_symbol, orderId, n_qty, n_LmtPrice, s_action, s_orderType, s_oca, s_parentId, n_button_create, n_button_close, open_status):

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

    logging.info('Trigger %s', ctx.triggered_id)

    if ctx.triggered_id == "modalOrdenUpdate_boton_close":
        return s_symbol, orderId, n_qty, n_LmtPrice, s_action, s_orderType, s_oca, s_parentId, False

    if ctx.triggered_id == "modalOrdenUpdate_boton_update":
        contrato = globales.G_RTlocalData_.contractGetBySymbol (s_symbol)
        orden = globales.G_RTlocalData_.orderGetByOrderId(orderId)
        secType = contrato['contract'].secType

        error = False

        try:
            n_qty = int (n_qty)
        except:
            error = True
        
        if s_orderType in ['LMT', 'STP']:
            try:
                n_LmtPrice = float (n_LmtPrice)
            except:
                error = True
        else:
            n_LmtPrice = 0

        orden['order'].totalQuantity = n_qty
        if s_orderType == 'LMT':
            orden['order'].lmtPrice = n_LmtPrice
        if s_orderType == 'STP':
            orden['order'].auxPrice = n_LmtPrice
            
        if error == False:
            logging.info ('Vamos a actualizar la orden con:')
            logging.info ('  Symbol: %s', s_symbol)
            logging.info ('  secType: %s', secType)
            logging.info ('  Action: %s', s_action)
            logging.info ('  Type: %s', s_orderType)
            logging.info ('  LmtPrice: %s', n_LmtPrice)
            logging.info ('  Qty: %s', n_qty)
            try:
                result = globales.G_RTlocalData_.orderUpdateOrder (s_symbol, contrato['contract'], orden['order'])
                result = True
            except:
                logging.error ("Exception occurred", exc_info=True)

            return s_symbol, orderId, n_qty, n_LmtPrice, s_action, s_orderType, s_oca, s_parentId, False
        else:
            return no_update

    if 'orderId' in ctx.triggered_id:
        orderId = int(ctx.triggered_id['orderId'])
        orden = globales.G_RTlocalData_.orderGetByOrderId(orderId)
        gConId = orden['contractId']
        contrato = globales.G_RTlocalData_.contractGetContractbyGconId (gConId)

        #ahora hay que borrarla
        logging.info('Queremos actualizar la orden %s', str(orderId))

        contractText = ''
        n_qty = 0
        n_LmtPrice = 0
        s_action = ''
        s_orderType = ''
        s_oca = ''
        s_parentId = ''
    
        if contrato != None and 'fullSymbol' in contrato:
            contractText = contrato['fullSymbol']

        if orden != None and 'order' in orden:
            n_qty = orden['order'].totalQuantity
            s_action = orden['order'].action
            s_orderType = orden['order'].orderType
            s_oca = orden['order'].ocaGroup
            s_parentId = orden['order'].parentId
            if s_orderType == 'LMT':
                n_LmtPrice = orden['order'].lmtPrice
            if s_orderType == 'STP':
                n_LmtPrice = orden['order'].auxPrice
    
        return contractText, orderId, n_qty, n_LmtPrice, s_action, s_orderType, s_oca, s_parentId, True

    # Para todos los demas:
    return no_update

#Callback para actualizar fila de valores de Ordenes
@callback(
    Output({'role':'orden_header', 'orderId': MATCH}, "children"),
    Input({'role': 'IntervalOrdersLine', 'orderId': MATCH}, 'n_intervals'),
    prevent_initial_call = True,
)
def actualizarFilaOrdenes (n_intervals):
    if not ctx.triggered_id:
        raise PreventUpdate
    logging.debug ('Actualizando Ordenes Fila')
    orderId = ctx.triggered_id['orderId']
    try:
        orderId = int (orderId)
    except:
        logging.error ('Error en la ordenId al actualizar lista')
    orden = globales.G_RTlocalData_.orderGetByOrderId(orderId)
    resp = ordenesObtenerFilas (orden, True )
    return resp

# Callback para borrar ordenes individualmente
@callback(
    Output("order_cancel_orderId", "value"),
    Output("modal_cancelOrder_main", "is_open"),
    Input({'role': 'boton_order_cancel', 'orderId': ALL}, "n_clicks"),
    Input("modal_cancelOrder_boton_cancel", "n_clicks"),
    Input("modal_cancelOrder_boton_close", "n_clicks"),
    Input("order_cancel_orderId", "value"),
    State("modal_cancelOrder_main", "is_open"), prevent_initial_call = True,
)
def cancelOrder (n_button_open, n_button_cancel, n_button_close, orderId, open_status):

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

    if ctx.triggered_id == "modal_cancelOrder_boton_close":
        return None, False
    
    if ctx.triggered_id == "modal_cancelOrder_boton_cancel":
    
        #ahora hay que borrarla
        logging.info('[Orden (%s)] CANCEL esta orden desde GUI', str(orderId))
        #return no_update, no_update, no_update
    
        try:
            result = globales.G_RTlocalData_.orderCancelByOrderId (orderId)
            result = True
        except:
            logging.error ("Exception occurred", exc_info=True)

        return None, False
            

    if 'orderId' in ctx.triggered_id:
        orderId = int(ctx.triggered_id['orderId'])
        return orderId, True

# Callback para pedir order update
@callback(
    Output({'role': 'ZoneButtonReqOrderUpdate'}, "n_clicks"),   # Dash obliga a poner un output.
    Input({'role': 'ZoneButtonReqOrderUpdate'}, "n_clicks"), 
    prevent_initial_call = True,
)
def pedirOrderUpdate(n_button_open):
    
    if not ctx.triggered_id:
        return no_update

    # Esto es por si las moscas
    if n_button_open == 0:
        raise PreventUpdate

    logging.info ('Pedimos update de ordenes')
    globales.G_RTlocalData_.appObj_.reqAllOpenOrders()
    
    return no_update