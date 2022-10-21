from flask import Flask
from dash import Dash, html, dcc, MATCH, Input, Output, State, ctx
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import globales
import logging
import random
import pandas as pd


logger = logging.getLogger(__name__)


appDashFE_ = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
appDashFE_.title = "IB RODSIC"

def layout_contratos_tab ():

    data = globales.G_RTlocalData_.contratoReturnListAll()
    ContentItems = []
    item = 0
    #################################
    # Preparacion de Tab de contratos
    for contrato in data:
        posicion = globales.G_RTlocalData_.positionGetByGconId(contrato['gConId'])
        insideDetailsData = []
        if posicion == None:
            posQty = "0"
            posavgCost = "0"
        else:
            posQty = str(posicion['pos_n']) 
            posavgCost = str(posicion['avgCost'])
        priceBuy = str(contrato['currentPrices']['BUY'])
        priceSell = str(contrato['currentPrices']['SELL'])
        priceLast = str(contrato['currentPrices']['LAST'])
        symbol = globales.G_RTlocalData_.contractSummaryBrief(contrato['gConId'])
        # Cada fila de cabecera
        headerRow = dbc.Row(
                [
                    dbc.Col(dbc.Button(symbol,id={'role': 'boton', 'index': item}), className = 'bg-primary mr-1', width = 4),
                    dbc.Col(html.Div(posQty), className = 'bg-primary mr-1', width = 1),
                    dbc.Col(html.Div(posavgCost), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div(priceBuy), className = 'bg-success', width = 1),
                    dbc.Col(html.Div(priceSell), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div(priceLast), className = 'bg-primary', width = 1),
                    dbc.Col(html.Div("Comment"), className = 'bg-primary', width = 3),
                ], className = 'text-white mb-1',
        )        
        # Los detalles que se ocultan. Dos columnas, detalles y figura 
        # Primero los detalles
        insideDetailsData.append(html.Div(children = "ConId: " + str(contrato['contract'].conId), style = {"margin-left": "40px"}))
        insideDetailsData.append(html.Div(children = "Symbol: " + str(contrato['contract'].localSymbol), style = {"margin-left": "40px"}))
        insideDetailsData.append(html.Div(children = "secType: " + str(contrato['contract'].secType), style = {"margin-left": "40px"}))
        if contrato['contract'].secType == "BAG":
            for leg in contrato['contract'].comboLegs:
                insideDetailsData.append(html.Div(children = "Leg: ", style = {"margin-left": "40px"}))
                insideDetailsData.append(html.Div(children = "ConId: " + str(leg.conId), style = {"margin-left": "80px"}))
                insideDetailsData.append(html.Div(children = "Action: " + str(leg.action), style = {"margin-left": "80px"}))
                insideDetailsData.append(html.Div(children = "Ratio: " + str(leg.ratio), style = {"margin-left": "80px"}))
                for contratoLeg in data:
                    if contratoLeg['contract'].conId == leg.conId:
                        insideDetailsData.append(html.Div(children = "LocalSymbol: " + contratoLeg['contract'].localSymbol, style = {"margin-left": "80px"}))
                        insideDetailsData.append(html.Div(children = "LastOrderDate: " + contratoLeg['contract'].lastTradeDateOrContractMonth, style = {"margin-left": "80px"}))
                        break
        elif contrato['contract'].secType == "FUT":
            insideDetailsData.append(html.Div(children = "Date: " + str(contrato['contract'].lastTradeDateOrContractMonth), style = {"margin-left": "40px"}))

        # El grafico
        #fig = px.line(contrato['dbPandas'].dbGetDataframe(), x="timestamp", y="LAST", title="LAST Evolution") 
        #fig.update_layout(xaxis = dict(type="category")) # Para que no deje los vacios de fecha de cierre
        df_today = contrato['dbPandas'].dbGetDataframeToday()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_today['timestamp'], y=df_today["LAST"], mode="lines", connectgaps = True))
        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
                dict(bounds=[20.25, 14.5], pattern="hour"),  # hide hours outside of 9.30am-4pm
                #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
            ]
        )
        graphColumn = html.Div(
            dcc.Graph(
                    id={'role': 'graphDetails', 'index': item},
                    figure = fig 
            )
        )
        # Todo lo que se oculta junto
        collapseDetails = dbc.Collapse(
            dbc.Row(
                [
                    dbc.Col(insideDetailsData),
                    dbc.Col(graphColumn),
                ],
            ),
            id={'role': 'colapse', 'index': item},
            is_open=False,
        )

        ContentItems.append({"header": headerRow, "details": collapseDetails})
        item += 1

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
                    dbc.Col(html.Div("Comment"), className = 'bg-primary', width = 3),
                ], className = 'mb-3 text-white'
                ),
            ]

    for line in ContentItems:
      
        tabContratos.append(line['header'])
        tabContratos.append(line['details'])

    return tabContratos

def layout_strategies_tab():
    #contracts_ = globales.G_RTlocalData_.contratoReturnListAll()
    #strategiesIndex_ = globales.G_RTlocalData_.strategies_.strategyIndexGetAll()
    strategyMariposaVerano_ = globales.G_RTlocalData_.strategies_.strategyPentagramaObj_.strategyPentagramaGetAll()
    logging.info (strategyMariposaVerano_)
    #{'symbol': lineSymbol, 'currentPos': lineCurrentPos, 'UpperOrderId': lineUpperOrderId, 'UpperOrderPermId': lineUpperOrderPermId, 'LowerOrderId': lineLowerOrderId, 'LowerOrderPermId': lineLowerOrderPermId, 'zones': zones}

    item = 0
    ContentItems = []
    ####################################
    # Preparacion de Tab de Estratgias
    for estrategia in strategyMariposaVerano_:
        symbol = estrategia['symbol']
        posQty = estrategia['currentPos']
        stratEnabled = estrategia['stratEnabled']
        contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
        # Cabecera para cada contrato con estrategia
        headerRow = dbc.Row(
                [
                    dbc.Col(dbc.Button(symbol,id={'role': 'boton', 'index': item}), className = 'bg-primary mr-1', width = 4),
                    dbc.Col(html.Div(posQty), className = 'bg-primary mr-1', width = 1),
                    dbc.Col(html.Div(""), className = 'bg-primary mr-1', width = 6),
                    dbc.Col(dbc.Switch(id={'role': 'switchStratEnabled', 'index': item}, value = stratEnabled), className = 'bg-primary mr-1', width = 1),
                ], className = 'text-white mb-1',
        )
        # El grafico que va escondido


        fig1 = go.Figure()
        df_comp = contrato['dbPandas'].dbGetDataframeComp()
        fig1.add_trace(go.Candlestick(x=df_comp.index, open=df_comp['open'], high=df_comp['high'],low=df_comp['low'],close=df_comp['close']))
        limitList= []
        for zone in estrategia['zones']:       
            if zone['limitUp'] not in limitList:
                zoneborder = [zone['limitUp']] * len (df_comp.index)
                fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_color="gray", line_width=1, connectgaps = True, fill=None))
                limitList.append(zone['limitUp'])
            if zone['limitDown'] not in limitList:
                zoneborder = [zone['limitDown']] * len (df_comp.index)
                fig1.add_trace(go.Scatter(x=df_comp.index, y=zoneborder, mode="lines", line_color="gray", line_width=1, connectgaps = True, fill=None))
        fig1.update_layout(showlegend=False, 
                           xaxis_rangeslider_visible=False, 
                           title_text='Historico (15min)', 
                           title_x = 0.5,
                           title_xanchor = 'center')
        
        fig1.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
                dict(bounds=[20.25, 14.5], pattern="hour"),  # hide hours outside of 9.30am-4pm
                #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
            ]
        )
        #fig1.update_layout(xaxis = dict(type="category"))

        graphColumn1 = html.Div(
            dcc.Graph(
                    id={'role': 'graphDetailsComp', 'gConId': str(contrato['gConId'])},
                    animate = False,
                    figure = fig1
            )
        )

        fig2 = layout_getFigureToday(estrategia)   # Lo tengo en una funcion para que sea facil actualizar

        random_wait = random.randint(0,1000) + 4000

        graphColumn2 = html.Div([
            dcc.Graph(
                    id={'role': 'graphDetailsToday', 'gConId': str(contrato['gConId'])},
                    animate = False,
                    figure = fig2
            ),
            dcc.Interval(
                id={'role': 'IntervalgraphToday', 'gConId': str(contrato['gConId'])},
                interval= random_wait, # in milliseconds
                n_intervals=0
            )
        ])
        
        # Los detalles de la estrategia (escondidos)
        
        insideDetailsOrdenes = []
        insideDetailsOrdenes.append(html.Div(children = "Posiciones de la Estrategia: " + str(estrategia['currentPos'])))
        insideDetailsOrdenes.append(html.Div(children = "Orden Superior Actual (OrderId/PermId): " + str(estrategia['UpperOrderId']) + '/' + str(estrategia['UpperOrderPermId'])))
        insideDetailsOrdenes.append(html.Div(children = "Orden Inferior Actual (OrderId/PermId): " + str(estrategia['LowerOrderId']) + '/' + str(estrategia['LowerOrderPermId'])))

        zonasFilaHeader = []
        zonasFilaBorder = []
        zonasFilaHeader.append(dbc.Col(''))
        zonasFilaBorder.append(dbc.Col('Fronteras', align="center"))
        #zonasFilaLower.append(dbc.Col('LimitDwn'))
        itemZ = 1
        for zone in estrategia['zones']:
            val1 = zone['limitUp']
            val2 = zone['limitDown']
            
            zonasFilaHeader.append(dbc.Col('L' + str(itemZ), className="text-center"))
            zonasFilaBorder.append(dbc.Col(dbc.Input(id="input", placeholder=val1, type="text", className="text-end")))
            if itemZ == len(estrategia['zones']):
                zonasFilaHeader.append(dbc.Col('L' + str(itemZ+1), className="text-center"))
                zonasFilaBorder.append(dbc.Col(dbc.Input(id="input", placeholder=val2, type="text", className="text-end")))
            itemZ += 1 
        
        insideDetailsZonas = []
        insideDetailsZonas.append(dbc.Row(zonasFilaHeader))
        insideDetailsZonas.append(dbc.Row(zonasFilaBorder))
        insideDetailsZonas.append(dbc.Row(dbc.Input(id={'role': 'input', 'gConId': str(contrato['gConId'])}, placeholder='1', type="text", className="text-end")))
        #insideDetailsZonas.append(dbc.Row(zonasFilaLower))
        
        insideDetails = []
        insideDetails.append(dbc.Col(insideDetailsOrdenes))
        insideDetails.append(dbc.Col(insideDetailsZonas))
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
                        insideDetails,
                )
            ],
            id={'role': 'colapse', 'index': item},
            is_open=False,
            className = 'mb-3'
        )
        item += 1   
        ContentItems.append({"header": headerRow, "details": collapseDetails})

    #################################
    # Ahora creamos el tab de estrategias usando la info anterior
    tabEstrategias = [
            dbc.Row(
                [
                    html.H1("Lista de Estrategias", className='text-left text-secondary mb-4 display-4'),
                    html.Hr()
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(html.Div("Symbol"), className = 'bg-primary mr-1', width = 4),
                    dbc.Col(html.Div("Pos"), className = 'bg-primary mr-1', width = 1),
                    dbc.Col(html.Div("Comment"), className = 'bg-primary', width = 6),
                    dbc.Col(html.Div("Enabled"), className = 'bg-primary', width = 1),
                ], className = 'mb-3 text-white'
                ),
            ]

    for line in ContentItems:
        tabEstrategias.append(line['header'])
        tabEstrategias.append(line['details'])

    return tabEstrategias

def layout_getFigureToday (estrategia):
    symbol = estrategia['symbol']
    contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
    dfToday = contrato['dbPandas'].dbGetDataframeToday()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=dfToday['timestamp'], y=dfToday["LAST"], mode="lines", line_color="crimson", connectgaps = True))
    limitList= []
    for zone in estrategia['zones']:       
        if zone['limitUp'] not in limitList:
            zoneborder = [zone['limitUp']] * len (dfToday.index)
            fig2.add_trace(go.Scatter(x=dfToday["timestamp"], 
                                      y=zoneborder, 
                                      mode="lines", 
                                      line_color="gray", 
                                      line_width=1, 
                                      connectgaps = True, 
                                      fill=None))
            limitList.append(zone['limitUp'])
        if zone['limitDown'] not in limitList:
            zoneborder = [zone['limitDown']] * len (dfToday.index)
            fig2.add_trace(go.Scatter(x=dfToday["timestamp"], 
                                      y=zoneborder, 
                                      mode="lines", 
                                      line_color="gray", 
                                      line_width=1, 
                                      connectgaps = True, 
                                      fill=None))
    fig2.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
            dict(bounds=[20.25, 14.5], pattern="hour"),  # hide hours outside of 9.30am-4pm
            #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
        ]
    )

    rannn = str(random.randint(0,1000))
    logging.info ('Grafico actualizado con %s', rannn)
    fig2.update_layout(showlegend=False, 
                       title_text='Datos Tiempo Real Hoy'+rannn, 
                       title_x = 0.5,
                       title_xanchor = 'center')

    return fig2


def layout_init():
    chil1 = [
        html.H1(
            children="Prueba Front-End IB",
            style={"textAlign": "center"}
        ),
    ]

    layout = html.Div(
        id="parent",
        children=chil1
    )
    #return layout
    if globales.G_RTlocalData_ == None:
        return layout
    
    tabs = html.Div(
        [
            dbc.Tabs(
                [
                    dbc.Tab(label="Estrategias", tab_id="tab-estrat"),
                    dbc.Tab(label="Contratos", tab_id="tab-contrat"),
                ],
                id="tabs",
                active_tab="tab-contrat",
            ),
            html.Div(id="tabContent"),
        ]
    )

    layout = dbc.Container(tabs)

    return layout

appDashFE_.layout = layout_init   # Sin parentesis para que pille la funcion, no el valor

# Callback para cambiar tab
@appDashFE_.callback(Output("tabContent", "children"), [Input("tabs", "active_tab")])
def switch_tab(at):
    if at == "tab-contrat":
        return layout_contratos_tab()
    elif at == "tab-estrat":
        return layout_strategies_tab()
    return html.P("This shouldn't ever be displayed...")

# Callback para colapsar o mostrar filas
@appDashFE_.callback(
    Output({'role': 'colapse', 'index': MATCH}, "is_open"),
    Input({'role': 'boton', 'index': MATCH}, "n_clicks"),
    State({'role': 'colapse', 'index': MATCH}, "is_open"),
)
def toggle_left(n_button, is_open):
    if n_button:
        return not is_open
    return is_open

# Callbacl para actualizar graphs de today
@appDashFE_.callback(
    Output({'role': 'input', 'gConId': MATCH}, 'placeholder'),
    Output({'role': 'graphDetailsToday', 'gConId': MATCH}, 'figure'),
    Input({'role': 'IntervalgraphToday', 'gConId': MATCH}, 'n_intervals')
)
def update_graph_live(n_int):
    if not ctx.triggered_id:
        return None,None
    gConId = str(ctx.triggered_id.gConId)
    strategyMariposaVerano_ = globales.G_RTlocalData_.strategies_.strategyPentagramaObj_.strategyPentagramaGetAll()
    for estrategia in strategyMariposaVerano_:
        symbol = estrategia['symbol']
        contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
        if not contrato:
            return None,None
        if str(contrato['gConId']) == gConId:
            logging.info ("Son iguales")
            fig2 = layout_getFigureToday(estrategia)
            #fig2.update_layout(transition_duration=500)
            ret1 = str(random.randint(0,1000))
            return ret1, fig2

    logging.info ("No he encontrado la figura")


'''
@appDashFE_.callback(
    Output({'role': 'graphDetails', 'index': MATCH}, "figure"), Input(ThemeChangerAIO.ids.radio("theme"), "value"),
)
def update_graph_theme(theme):
    return px.bar(
        df, x="Fruit", y="Amount", color="City", barmode="group", template=template_from_url(theme)
    )
'''