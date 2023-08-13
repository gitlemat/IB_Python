from webFE.webFENew_Utils import formatCurrency
from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
from dash import html
from dash import dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import globales
import logging
import random

logger = logging.getLogger(__name__)

def insideDetailsPentagramaRu (estrategia, graphColumn1, graphColumn2):
    # Y las tablas con ordenes

    symbol = estrategia['symbol']

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

    # El boton de recarga

    insideDetailsBotonesZonas = []
    insideDetailsBotonesZonas.append(dbc.Row(dbc.Button("Actualizar desde Fichero", id={'role': 'ZoneButtonReload', 'strategy':'PentagramaRu', 'symbol': symbol}, className="me-2", n_clicks=0)))


    # Todo lo que se oculta junto
    collapseDetails = dbc.Collapse(
        [
            dbc.Row(
                [
                    dbc.Col(graphColumn1, width=6),
                    dbc.Col(graphColumn2, width=6)
                ]
            ),
            dbc.Row(
                    insideDetailsBotonesZonas,
            ),
            dbc.Row(
                    insideOrdenes,
            )
        ],
        id={'role': 'colapse_strategy', 'strategy':'PentagramaRu', 'symbol': symbol},
        is_open=False,
        className = 'mb-3'
    )

    return collapseDetails

def layout_getFigureHistoricoPenRu (estrategia):

    symbol = estrategia['symbol']
    strategyType = estrategia['type']
    contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
    if not contrato:
        logging.error ("Error cargando grafico historico de %s. No tenemos el contrato cargado en RT_Data", symbol)
        return no_update

    fig1 = go.Figure()

    if contrato['dbPandas']:
        df_comp = contrato['dbPandas'].dbGetDataframeComp()
        
        fig1.add_trace(go.Candlestick(x=df_comp.index, open=df_comp['open'], high=df_comp['high'],low=df_comp['low'],close=df_comp['close']))
        fig1 = addZonesLinesHistoricoRu (fig1, estrategia, df_comp)

    
    fig1.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
            dict(bounds=[21.1, 15], pattern="hour"),  # hide hours outside of 9.30am-4pm
            #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
        ]
    )

    fig1.update_layout(showlegend=False, 
                       xaxis_rangeslider_visible=False, 
                       title_text='Historico (15min)', 
                       title_x = 0.5,
                       title_xanchor = 'center',
                       margin=dict(l=10, r=10, t=40, b=40))

    return fig1


def addZonesLinesHistoricoRu (fig1, estrategia, df_comp):
    limitList= []
    for zone in estrategia['classObject'].zones_: 
        '''  
        ordenMain = globales.G_RTlocalData_.orderGetByOrderId (zone['OrderId'])
        ordenSL = globales.G_RTlocalData_.orderGetByOrderId (zone['OrderIdSL'])
        ordenTP = globales.G_RTlocalData_.orderGetByOrderId (zone['OrderIdTP'])

        if zone['Price'] not in limitList:
            zoneborder = [zone['Price']] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_color="gray", line_width=1, connectgaps = True, fill=None))
            limitList.append(zone['Price'])
        if zone['PrecioSL'] not in limitList:
            zoneborder = [zone['PrecioSL']] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_dash='dash', line_color="gray", line_width=1, connectgaps = True, fill=None))
            limitList.append(zone['PrecioSL'])
        if zone['PrecioTP'] not in limitList:
            zoneborder = [zone['PrecioTP']] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_dash='dash', line_color="gray", line_width=1, connectgaps = True, fill=None))
            limitList.append(zone['PrecioTP'])

        '''
        ordenMain = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderId_)
        ordenSL = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderIdSL_)
        ordenTP = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderIdTP_)

        if zone['orderBlock'].Price_ not in limitList:
            zoneborder = [zone['orderBlock'].Price_] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_color="gray", line_width=1, connectgaps = True, fill=None))
            limitList.append(zone['orderBlock'].Price_)
        if zone['orderBlock'].PrecioSL_ not in limitList:
            zoneborder = [zone['orderBlock'].PrecioSL_] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_dash='dash', line_color="gray", line_width=1, connectgaps = True, fill=None))
            limitList.append(zone['orderBlock'].PrecioSL_)
        if zone['orderBlock'].PrecioTP_ not in limitList:
            zoneborder = [zone['orderBlock'].PrecioTP_] * len (df_comp.index)
            fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_dash='dash', line_color="gray", line_width=1, connectgaps = True, fill=None))
            limitList.append(zone['orderBlock'].PrecioTP_)


    return fig1

def layout_getFigureTodayPenRu (estrategia, update = False):
    symbol = estrategia['symbol']
    strategyType = estrategia['type']
    contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
    if not contrato:
        logging.error ('Error cargando grafico de Hoy de %s. No tenemos el contrato cargado en RT_Data', symbol)
        return no_update
    if (contrato['dbPandas'].toPrint == False) and (update == True):
        logging.debug ('Grafico no actualizado. No hay datos nuevos')
        return no_update
    dfToday = contrato['dbPandas'].dbGetDataframeToday()
    fig2 = go.Figure()

    # Valores de LAST
    fig2.add_trace(go.Scatter(x=dfToday.index, y=dfToday["BID"], mode="lines", line_color="blue", connectgaps = True))
    fig2.add_trace(go.Scatter(x=dfToday.index, y=dfToday["ASK"], mode="lines", line_color="green", connectgaps = True))
    fig2.add_trace(go.Scatter(x=dfToday.index, y=dfToday["LAST"], mode="lines", line_color="crimson", connectgaps = True))
    
    # Y las zonas
    ifig2 = addZonesLinesTodayRu (fig2, estrategia, dfToday)

    fig2.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
            dict(bounds=[20.25, 15.16], pattern="hour"),  # hide hours outside of 9.30am-4pm
            #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
        ]
    )

    rannn = str(random.randint(0,1000))
    logging.debug ('Grafico actualizado con %s', rannn)
    fig2.update_layout(showlegend=False, 
                       title_text='Datos Tiempo Real Hoy', 
                       title_x = 0.5,
                       title_xanchor = 'center',
                       margin=dict(l=10, r=10, t=40, b=40))

    contrato['dbPandas'].toPrint = False

    return fig2

def addZonesLinesTodayRu (fig2, estrategia, dfToday):
    limitList= []
    for zone in estrategia['classObject'].zones_:  
        ''' 
        ordenMain = globales.G_RTlocalData_.orderGetByOrderId (zone['OrderId'])
        ordenSL = globales.G_RTlocalData_.orderGetByOrderId (zone['OrderIdSL'])
        ordenTP = globales.G_RTlocalData_.orderGetByOrderId (zone['OrderIdTP'])

        if zone['Price'] not in limitList:
            if ordenMain != None and ordenMain['params'] != None and 'status' in ordenMain['params']:
                if ordenMain['params']['status'] == 'Submitted':
                    zoneborder = [zone['Price']] * len (dfToday.index)
                    fig2.add_trace(go.Scatter(x=dfToday.index, y=zoneborder, mode="lines", line_color="gray", line_width=1, connectgaps = True, fill=None))
                    limitList.append(zone['Price'])
        if zone['PrecioSL'] not in limitList:
            if ordenSL != None and ordenSL['params'] != None and 'status' in ordenSL['params']:
                if ordenSL['params']['status'] == 'Submitted':
                    zoneborder = [zone['PrecioSL']] * len (dfToday.index)
                    fig2.add_trace(go.Scatter(x=dfToday.index, y=zoneborder, mode="lines", line_dash='dash', line_color="gray", line_width=1, connectgaps = True, fill=None))
                    limitList.append(zone['PrecioSL'])
        if zone['PrecioTP'] not in limitList:
            if ordenTP != None and ordenTP['params'] != None and 'status' in ordenTP['params']:
                if ordenTP['params']['status'] == 'Submitted':
                    zoneborder = [zone['PrecioTP']] * len (dfToday.index)
                    fig2.add_trace(go.Scatter(x=dfToday.index, y=zoneborder, mode="lines", line_dash='dash', line_color="gray", line_width=1, connectgaps = True, fill=None))
                    limitList.append(zone['PrecioTP'])

        '''
        ordenMain = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderId_)
        ordenSL = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderIdSL_)
        ordenTP = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderIdTP_)

        if zone['orderBlock'].Price_ not in limitList:
            if ordenMain != None and ordenMain['params'] != None and 'status' in ordenMain['params']:
                if ordenMain['params']['status'] == 'Submitted':
                    zoneborder = [zone['orderBlock'].Price_] * len (dfToday.index)
                    fig2.add_trace(go.Scatter(x=dfToday.index, y=zoneborder, mode="lines", line_color="gray", line_width=1, connectgaps = True, fill=None))
                    limitList.append(zone['orderBlock'].Price_)
        if zone['orderBlock'].PrecioSL_ not in limitList:
            if ordenSL != None and ordenSL['params'] != None and 'status' in ordenSL['params']:
                if ordenSL['params']['status'] == 'Submitted':
                    zoneborder = [zone['orderBlock'].PrecioSL_] * len (dfToday.index)
                    fig2.add_trace(go.Scatter(x=dfToday.index, y=zoneborder, mode="lines", line_dash='dash', line_color="gray", line_width=1, connectgaps = True, fill=None))
                    limitList.append(zone['orderBlock'].PrecioSL_)
        if zone['orderBlock'].PrecioTP_ not in limitList:
            if ordenTP != None and ordenTP['params'] != None and 'status' in ordenTP['params']:
                if ordenTP['params']['status'] == 'Submitted':
                    zoneborder = [zone['orderBlock'].PrecioTP_] * len (dfToday.index)
                    fig2.add_trace(go.Scatter(x=dfToday.index, y=zoneborder, mode="lines", line_dash='dash', line_color="gray", line_width=1, connectgaps = True, fill=None))
                    limitList.append(zone['orderBlock'].PrecioTP_)

    return fig2



def layout_getStrategyPenRuTableOrders (estrategia, update = False):

    #orden = globales.G_RTlocalData_.orderGetByOrderId(lOrderId)
    if estrategia['classObject'].ordersUpdated_ == False and update == True:
        logging.debug ('Tabla de ordenes en Strategia no actualizado. No hay datos nuevos')
        return no_update

    insideDetailsTableHeader = [
        html.Thead(
            html.Tr(
                [
                   html.Th(""), 
                   html.Th("Order Id"),
                   html.Th("Perm Id"),
                   html.Th("Lmt"),
                   html.Th("Type"),
                   html.Th("Status"),
                   html.Th("Qty"),
                ]
            )   
        )
    ]

    insideDetailsTableBodyInside = []

    for zone in estrategia['classObject'].zones_:
        #ordenParent = globales.G_RTlocalData_.orderGetByOrderId (zone['OrderId'])
        ordenParent = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderId_)
        if ordenParent:
            posParent = ordenParent['order'].totalQuantity
            typeParent = ordenParent['order'].orderType
            if ordenParent['params'] != None and 'status' in ordenParent['params']:
                statusParent = ordenParent['params']['status']
            else:
                statusParent = 'N/A'
            lmtParent = ordenParent['order'].lmtPrice
            if ordenParent['order'].orderType == 'STP':
                lmtParent = ordenParent['order'].auxPrice
            lmtParent = formatCurrency(lmtParent)
            if ordenParent['order'].action == 'SELL':
                posParent = posParent * (-1)
        else:
            posParent = 'N/A'
            lmtParent = 'N/A'
            typeParent = 'N/A'
            statusParent = 'N/A'

        #ordenTP = globales.G_RTlocalData_.orderGetByOrderId (zone['OrderIdTP'])
        ordenTP = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderIdTP_)
        if ordenTP:
            posTP = ordenTP['order'].totalQuantity
            typeTP = ordenTP['order'].orderType
            if ordenTP['params'] != None and 'status' in ordenTP['params']:
                statusTP = ordenTP['params']['status']
            else:
                statusTP = 'N/A'
            lmtTP = ordenTP['order'].lmtPrice
            if ordenTP['order'].orderType == 'STP':
                lmtTP = ordenTP['order'].auxPrice
            lmtTP = formatCurrency(lmtTP)
            if ordenTP['order'].action == 'SELL':
                posTP = posTP * (-1)
        else:
            posTP = 'N/A'
            lmtTP = 'N/A'
            typeTP = 'N/A'
            statusTP = 'N/A'

        #ordenSL = globales.G_RTlocalData_.orderGetByOrderId (zone['OrderIdSL'])
        ordenSL = globales.G_RTlocalData_.orderGetByOrderId (zone['orderBlock'].orderIdSL_)
        if ordenSL:
            posSL = ordenSL['order'].totalQuantity
            typeSL = ordenSL['order'].orderType
            if ordenSL['params'] != None and 'status' in ordenSL['params']:
                statusSL = ordenSL['params']['status']
            else:
                statusSL = 'N/A'
            lmtSL = ordenSL['order'].lmtPrice
            if ordenSL['order'].orderType == 'STP':
                lmtSL = ordenSL['order'].auxPrice
            lmtSL = formatCurrency(lmtSL)
            if ordenSL['order'].action == 'SELL':
                posSL = posSL * (-1)
        else:
            posSL = 'N/A'
            lmtSL = 'N/A'
            typeSL = 'N/A'
            statusSL = 'N/A'

        insideDetailsStratParent = html.Tr(
            [
                html.Td("Parent"), 
                #html.Td(str(zone['OrderId'])),
                #html.Td(str(zone['OrderPermId'])),
                html.Td(str(zone['orderBlock'].orderId_)),
                html.Td(str(zone['orderBlock'].orderPermId_)),
                html.Td(str(lmtParent)),
                html.Td(str(typeParent)),
                html.Td(str(statusParent)),
                html.Td(str(posParent)),
            ]
        )

        insideDetailsStratTP = html.Tr(
            [
                html.Td("T Profit", style={"textAlign": "right"}), 
                #html.Td(str(zone['OrderIdTP'])),
                #html.Td(str(zone['OrderPermIdTP'])),
                html.Td(str(zone['orderBlock'].orderIdTP_)),
                html.Td(str(zone['orderBlock'].orderPermIdTP_)),
                html.Td(str(lmtTP)),
                html.Td(str(typeTP)),
                html.Td(str(statusTP)),
                html.Td(str(posTP)),
            ]
        )

        insideDetailsStratSL = html.Tr(
            [
                html.Td("Stop Loss", style={"textAlign": "right"}), 
                #html.Td(str(zone['OrderIdSL'])),
                #html.Td(str(zone['OrderPermIdSL'])),
                html.Td(str(zone['orderBlock'].orderIdSL_)),
                html.Td(str(zone['orderBlock'].orderPermIdSL_)),
                html.Td(str(lmtSL)),
                html.Td(str(typeSL)),
                html.Td(str(statusSL)),
                html.Td(str(posSL)),
            ]
        )

        insideDetailsTableBodyInside.append(insideDetailsStratParent)
        insideDetailsTableBodyInside.append(insideDetailsStratTP)
        insideDetailsTableBodyInside.append(insideDetailsStratSL)


    insideDetailsTableBody = [html.Tbody(insideDetailsTableBodyInside)]
    estrategia['classObject'].ordersUpdated_ = False

    ret = dbc.Table(
        insideDetailsTableHeader + insideDetailsTableBody, 
        bordered=True
    )

    return ret

#Callback para actualizar tabla de ordenes en Strategy
@callback(
    Output({'role':'TableStrategyOrderDetails', 'strategy':'PentagramaRu', 'symbol': MATCH}, "children"),
    Input({'role': 'IntervalOrderTable', 'strategy':'PentagramaRu', 'symbol': MATCH}, 'n_intervals'),
    prevent_initial_call = True,
)
def actualizarTablaOrdenesStrategiesPenRu (n_intervals):
    if not ctx.triggered_id:
        raise PreventUpdate
    logging.debug ('Actualizando tabla ordenes estrategia')
    symbol = ctx.triggered_id['symbol']

    estrategia = globales.G_RTlocalData_.strategies_.strategyGetStrategyBySymbolAndType (symbol, 'PentagramaRu')
    resp = layout_getStrategyPenRuTableOrders (estrategia, True)

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

    # Aqui grabamos los zones
    logging.info ("Actualización de los ficheros de estrategia Ruben (%s)", symbol)
    globales.G_RTlocalData_.strategies_.strategyPentagramaRuObj_.strategyPentagramaRuReadFile ()

    return  no_update