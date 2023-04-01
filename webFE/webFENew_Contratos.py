from dash import html
from dash import dcc
from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
from dash.exceptions import PreventUpdate

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from webFE.webFENew_Utils import formatCurrency
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
                dbc.Col(html.H1("Lista de Contratos",
                                className='text-center text-primary mb-4'),
                        width=12)
            ),
            dbc.Row(
                [
                    dbc.Col(html.Div("Symbol"), className = 'bg-primary mr-1', width = 4),
                    dbc.Col(html.Div("Pos"), className = 'bg-primary mr-1', width = 1),
                    dbc.Col(html.Div("AvgPrice"), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("Buy"), className = 'bg-success', width = 1),
                    dbc.Col(html.Div("Sell"), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("Last"), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("Comment"), className = 'bg-primary', width = 2),
                    dbc.Col(html.Div("Order"), className = 'bg-primary', width = 1),
                ], className = 'mb-3 text-white'
                ),
            ]


    #################################
    # Preparacion de Tab de contratos
    for gConId, contrato in data.items():
        
        headerRowInn = contratosObtenerFilas (contrato, False)  
        random_wait = random.randint(0,2000) + 4000

        headerRow = html.Div(
            [
                html.Div(
                    headerRowInn, id ={'role':'contract_header', 'gConId': str(gConId)}
                ),
                dcc.Interval(
                    id={'role': 'IntervalContractLine', 'gConId': str(gConId)},
                    interval= random_wait, # in milliseconds
                    n_intervals=0
                )
            ]
        )

        insideDetailsData, graphColumn = contratosObtenerInsideDetails (contrato, data, False)

        # Todo lo que se oculta junto
        collapseDetails = dbc.Collapse(
            dbc.Row(
                [
                    dbc.Col(insideDetailsData, width = 5),
                    dbc.Col(graphColumn, width = 7),
                ],
            ),
            id={'role': 'colapseContract', 'gConId': str(gConId)},
            is_open=False,
        )        

        tabContratos.append(headerRow)
        tabContratos.append(collapseDetails)

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
    priceBuy = formatCurrency(contrato['currentPrices']['BUY'])
    priceSell = formatCurrency(contrato['currentPrices']['SELL'])
    priceLast = formatCurrency(contrato['currentPrices']['LAST'])
    symbol = contrato['fullSymbol']
    # Cada fila de cabecera
    headerRow = dbc.Row(
            [
                dbc.Col(dbc.Button(symbol,id={'role': 'botonContract', 'gConId': str(gConId)}), className = 'bg-primary mr-1', width = 4),
                dbc.Col(html.Div(posQty), className = 'bg-primary mr-1', width = 1),
                dbc.Col(html.Div(posavgCost), className = 'bg-primary', width = 1),
                dbc.Col(html.Div(priceBuy), className = 'bg-success', width = 1),
                dbc.Col(html.Div(priceSell), className = 'bg-primary', width = 1),
                dbc.Col(html.Div(priceLast), className = 'bg-primary', width = 1),
                dbc.Col(html.Div("Comment"), className = 'bg-primary', width = 2),
                dbc.Col(dbc.Button(html.I(className="bi bi-bag-plus me-2"),id={'role': 'boton_order_create', 'gConId': str(gConId)}), className = 'bg-primary', width = 1),
            ], className = 'text-white mb-1',
    )  

    return headerRow

def contratosObtenerInsideDetails (contrato, data, update = False):
    # Los detalles que se ocultan. Dos columnas, detalles y figura 
    # Primero los detalles
    gConId = contrato['gConId']
    insideDetailsData = []
    insideDetailsData.append(html.Div(children = "gConId: " + str(contrato['gConId']), style = {"margin-left": "40px"}))
    insideDetailsData.append(html.Div(children = "ConId: " + str(contrato['contract'].conId), style = {"margin-left": "40px"}))
    insideDetailsData.append(html.Div(children = "Symbol: " + str(contrato['contract'].localSymbol), style = {"margin-left": "40px"}))
    insideDetailsData.append(html.Div(children = "secType: " + str(contrato['contract'].secType), style = {"margin-left": "40px"}))
    if contrato['contract'].secType == "BAG":
        for leg in contrato['contract'].comboLegs:
            insideDetailsData.append(html.Div(children = "Leg: ", style = {"margin-left": "40px"}))
            insideDetailsData.append(html.Div(children = "ConId: " + str(leg.conId), style = {"margin-left": "80px"}))
            insideDetailsData.append(html.Div(children = "Action: " + str(leg.action), style = {"margin-left": "80px"}))
            insideDetailsData.append(html.Div(children = "Ratio: " + str(leg.ratio), style = {"margin-left": "80px"}))

            insideDetailsData.append(html.Div(children = "LocalSymbol: " + data[leg.conId]['contract'].localSymbol, style = {"margin-left": "80px"}))
            insideDetailsData.append(html.Div(children = "LastOrderDate: " + data[leg.conId]['contract'].lastTradeDateOrContractMonth, style = {"margin-left": "80px"}))

    elif contrato['contract'].secType == "FUT":
        insideDetailsData.append(html.Div(children = "Date: " + str(contrato['contract'].lastTradeDateOrContractMonth), style = {"margin-left": "40px"}))

    # El grafico
    #fig = px.line(contrato['dbPandas'].dbGetDataframe(), x="timestamp", y="LAST", title="LAST Evolution") 
    #fig.update_layout(xaxis = dict(type="category")) # Para que no deje los vacios de fecha de cierre
    fig = go.Figure()
    
    if contrato['dbPandas']:
        #df_today = contrato['dbPandas'].dbGetDataframeToday()
        #fig.add_trace(go.Scatter(x=df_today.index, y=df_today["LAST"], mode="lines", connectgaps = True))
        df_comp = contrato['dbPandas'].dbGetDataframeComp()
        fig.add_trace(go.Candlestick(x=df_comp.index, open=df_comp['open'], high=df_comp['high'],low=df_comp['low'],close=df_comp['close']))

    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
            dict(bounds=[20.25, 14.5], pattern="hour"),  # hide hours outside of 9.30am-4pm
            #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
        ]
    )
    fig.update_layout(showlegend=False, 
                       xaxis_rangeslider_visible=False, 
                       title_text='Historico (15min)', 
                       title_x = 0.5,
                       title_xanchor = 'center')
                       
    graphColumn = html.Div(
        dcc.Graph(
                id={'role': 'graphDetails', 'gConId': str(gConId)},
                figure = fig 
        )
    )

    return insideDetailsData, graphColumn

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

# Callback para borrar ordenes individualmente
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
def createOrder (n_button_open, s_symbol,  n_qty, n_LmtPrice, s_action, s_orderType, n_button_create, n_button_close, open_status):

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
            logging.info ('Vamos a crear una orden con:')
            logging.info ('  Symbol: %s', s_symbol)
            logging.info ('  secType: %s', secType)
            logging.info ('  Action: %s', s_action)
            logging.info ('  Type: %s', s_orderType)
            logging.info ('  LmtPrice: %s', n_LmtPrice)
            logging.info ('  Qty: %s', n_qty)
            try:
                result = globales.G_RTlocalData_.orderPlaceBrief (s_symbol, secType, s_action, s_orderType, n_LmtPrice, n_qty)
                result = True
            except:
                pass

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

