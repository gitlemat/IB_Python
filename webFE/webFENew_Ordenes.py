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
                    html.P("Lista de Ordenes", className='text-left text-secondary mb-4 ps-0 display-6'),
                    html.Hr()
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(html.Div("OrdenId"), className = 'bg-primary mr-1', width = 1),
                    dbc.Col(html.Div("Symbol"), className = 'bg-primary mr-1', width = 3),
                    dbc.Col(html.Div("Action"), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("Status"), className = 'bg-success', width = 1),
                    dbc.Col(html.Div("Fill Status"), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("LastFill"), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("Estrategia"), className = 'bg-primary', width = 3),
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
                dbc.Col(html.Div(symbol), className = 'bg-primary mr-1', width = 3),
                dbc.Col(html.Div(lAction), className = 'bg-primary', width = 1),
                dbc.Col(html.Div(lStatus), className = 'bg-success', width = 1),
                dbc.Col(html.Div(lFillState), className = 'bg-primary', width = 1),
                dbc.Col(html.Div(lLastFillPrice), className = 'bg-primary', width = 1),
                dbc.Col(html.Div(lStrategy), className = 'bg-primary', width = 3),
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

    lLmtPrice = formatCurrency (lLmtPrice)

    insideDetailsData = []
    insideDetailsData.append(html.Div(children = "gConId: " + lgConId, style = {"margin-left": "40px"}))
    insideDetailsData.append(html.Div(children = "PermId: " + lPermId, style = {"margin-left": "40px"}))
    insideDetailsData.append(html.Div(children = "Order Type: " + lorderType, style = {"margin-left": "40px"}))
    insideDetailsData.append(html.Div(children = "Limit Price: " + lLmtPrice, style = {"margin-left": "40px"}))
    insideDetailsData.append(html.Div(children = "Time in Force: " + lTif, style = {"margin-left": "40px"}))

    return insideDetailsData

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
    Output("modalErrorHeader", "children"),
    Output("modalErrorBody", "children"),
    Output("modal_error_main", "is_open"),
    Input({'role': 'boton_order_cancel', 'orderId': ALL}, "n_clicks"),
    Input("modal_boton_close", "n_clicks"),
    State("modal_error_main", "is_open"), prevent_initial_call = True,
)
def cancelOrder (n_button_open, n_button_close, open_status):

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

    responseHeader = ''
    responseBody = ''

    logging.debug('Trigger %s', ctx.triggered_id)

    if ctx.triggered_id == "modal_boton_close":
        return responseHeader, responseBody, False

    orderId = ctx.triggered_id['orderId'] 

    #ahora hay que borrarla
    logging.info('[Orden (%s)] CANCEL esta orden desde GUI', str(orderId))
    #return no_update, no_update, no_update

    
    try:
        result = globales.G_RTlocalData_.orderCancelByOrderId (orderId)
        result = True
    except:
        responseHeader = 'Error'
        responseBody = 'Error al cancelar la ordenId: ' + str(orderId)
        
    else:
        if result:
            responseHeader = 'Aceptado'
            responseBody = 'Cancelacion ' + str(orderId) + 'Orden Lanzada'
        else:
            responseHeader = 'Error'
            responseBody = 'Orden no encontrada'

    return responseHeader, responseBody, True