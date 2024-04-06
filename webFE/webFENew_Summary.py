from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
from dash import html
from dash import dcc
from dash import dash_table
from dash.dash_table.Format import Format, Group, Prefix, Scheme, Symbol
from dash.exceptions import PreventUpdate

import dash_bootstrap_components as dbc
from webFE.webFENew_Utils import formatCurrency, layout_getFigureHistorico
import logging
import globales
import random


logger = logging.getLogger(__name__)

def layout_summary_tab ():

    precios = create_preciosTop()

    tabSummary = [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.P("Global", className='text-left text-secondary mb-4 ps-0 display-6')
                    ]
                ),
                dbc.Col(
                    [
                        html.Div(
                            precios, id ={'role':'precios_header'}
                        ),
                        dcc.Interval(
                            id={'role': 'Intervalprecios_header'},
                            interval= 3000, # in milliseconds
                            n_intervals=0
                        )
                    ]
                ),
                html.Hr()
            ]
        ),
    ]

    contractList = globales.G_RTlocalData_.contratoReturnDictAll()
    if globales.G_RTlocalData_.strategies_ == None:
        return tabSummary
        
    strategyList = globales.G_RTlocalData_.strategies_.strategyGetAll()
    
    all_cards = []
    included_contracts = []
    for estrategia in strategyList:
        symbol = estrategia['symbol']
                
        contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
        if not contrato:
            logging.error ('Error cargando estrategia Headerde %s. No tenemos el contrato cargado en RT_Data', symbol)
            return no_update

        included_contracts.append(symbol)

        this_card = create_card (contrato, estrategia)

        data = {'card':this_card, 'symbol': symbol, 'stratType': estrategia['type']}

        all_cards.append(data)

    for gConId, contrato in contractList.items():
        indirect = globales.G_RTlocalData_.contractIndirectoGet (gConId) # Podria leer de contrato, pero es una guarregria (como mucho de lo que hay aqui)
        logging.debug ('Contrato Indirecto %s', indirect)
        if indirect:
            continue
        symbol = contrato['fullSymbol']

        if symbol in included_contracts:
            continue

        this_card = create_card (contrato, None)

        data = {'card':this_card, 'symbol': symbol, 'stratType': ''}

        all_cards.append(data)

    # Ahora añadimos la lista de execs a tabSummary

    df_execs = globales.G_RTlocalData_.strategies_.strategyGetAllExecs()

    if len(df_execs) > 0:
        logging.debug ('%s',df_execs )
        df_execs.sort_index(ascending=False, inplace = True)
        df_execs['time'] = df_execs.index.strftime("%d/%m/%Y - %H:%M:%S")
        #df_execs.sort_values(by=['time'], inplace=True, ascending=False)

    columnas = [
        {'id': "time", 'name': "Fecha", 'type': 'datetime'},
        {'id': "OrderId", 'name': "OrderId", 'type': 'numeric'},
        {'id': "Side", 'name': "Side", 'type': 'text'},
        {'id': "FillPrice", 'name': "Precio", 'type': 'numeric', 'format': Format(symbol=Symbol.yes, symbol_prefix='$', precision=3)},
        {'id': "Quantity", 'name': "Qty", 'type': 'numeric'},
        {'id': "RealizedPnL", 'name': "PnL", 'type': 'numeric', 'format': Format(symbol=Symbol.yes, symbol_prefix='$', precision=3)},
        {'id': "Commission", 'name': "Comisión", 'type': 'numeric', 'format': Format(symbol=Symbol.yes, symbol_prefix='$', precision=3)},
        {'id': "Strategy", 'name': "Estrategia", 'type': 'text'},
    ]

    tablaExecs = dbc.Card([
        dash_table.DataTable(
            data=df_execs.to_dict('records'), 
            columns = columnas,
            page_size=20,
            filter_action="native",
            )
        ],
        className='text9-7'
    )
    #logging.info ('%s', df_execs)

    for i in range(0, len(all_cards), 2):
        logging.debug ('Card: %d, %d', i, len(all_cards))
        #column1 = dbc.Col(all_cards[i]['card'], id='summary-card-l-'+str(i), md=6)
        #dbc.Col(html.Div("PnL (daily/real/unreal)"), id='contract-header-comm', className = 'text9-7 d-none d-md-block bg-primary', md = 2),
        column1 = dbc.Col(
            [
                html.Div(
                    all_cards[i]['card'], id={'role':'summary-card', 'symbol':all_cards[i]['symbol'], 'stratType':all_cards[i]['stratType']}
                ),
                dcc.Interval(
                    id={'role': 'Interval-summary-card', 'symbol':all_cards[i]['symbol'], 'stratType':all_cards[i]['stratType']},
                    interval= 3000, # in milliseconds
                    n_intervals=0
                )
            ], md=6
        )
            
        column2 = None
        if i + 1 < len(all_cards):
            #column2 = dbc.Col(all_cards[i+1]['card'], id={'role':'summary-card', 'symbol':all_cards[i+1]['symbol'], 'stratType':all_cards[i+1]['stratType']}, md=6)
            column2 = dbc.Col(
                [
                    html.Div(
                        all_cards[i+1]['card'], id={'role':'summary-card', 'symbol':all_cards[i+1]['symbol'], 'stratType':all_cards[i+1]['stratType']}
                    ),
                    dcc.Interval(
                        id={'role': 'Interval-summary-card', 'symbol':all_cards[i+1]['symbol'], 'stratType':all_cards[i+1]['stratType']},
                        interval= 3000, # in milliseconds
                        n_intervals=0
                    )
                ], md=6
            )
        row = dbc.Row(
            [
                column1,
                column2,
            ]
        )  
        tabSummary.append(row)

    row = dbc.Row(
        [
            tablaExecs,
        ]
    ) 

    tabSummary.append(row)


    return tabSummary

def create_preciosTop ():
    color_rojo = '#ff0000'
    color_verde = '#366b22'
    color_negro = '#000000'

    if globales.G_RTlocalData_.accountPandas_ == None:
        return None
    dfAccountYesterday = globales.G_RTlocalData_.accountPandas_.dbGetAccountDataUntilYesterday()
    #dfAccountYesterday = dfAccountYesterday.astype({'NetLiquidation':'float'})
    dfAccountToday = globales.G_RTlocalData_.accountPandas_.dbGetAccountDataLast()


    try:

        NetLiqLast = float(dfAccountToday['NetLiquidation'])
    except:
        NetLiqLast = 0.0

    try:
        NetLiqYesterday = float(dfAccountYesterday.iloc[-1]['NetLiquidation'])
    except:
        NetLiqYesterday = 0.0

    if NetLiqYesterday != 0:
        increment = (NetLiqLast - NetLiqYesterday) / NetLiqYesterday * 100
    else:
        increment = 0

    diff = NetLiqLast - NetLiqYesterday

    logging.debug ('NetLiq:\n%s\n%s\n%s\n%s', NetLiqYesterday, NetLiqLast, diff, increment)

    if diff < 0:
        priceLastColor = color_rojo
    else:
        priceLastColor = color_verde

    NetLiqLast = formatCurrency(NetLiqLast)
    diff = formatCurrency(diff)
    increment = "{:,.2f}".format(increment)

    h6priceList1 = html.Div(str(NetLiqLast) +"€", style={'color':color_negro},className='text20-9')
    h6priceList2 = html.Div(str(diff) + "€", style={'color':priceLastColor},className='text9-7')
    h6priceList3 = html.Div("(" + str(increment) + "%)", style={'color':priceLastColor},className='text9-7')

    precios = html.Span(
        [
            h6priceList1,
            html.Div([h6priceList2,h6priceList3])
        ], className="gap-2 d-flex justify-content-end"
    )

    return precios

def create_card (contrato, estrategia):
    if contrato == None:
        return None
    if contrato['dbPandas'] == None:
        return None
    symbol = contrato['fullSymbol']
    priceBuy = formatCurrency(contrato['currentPrices']['BUY'])
    priceSell = formatCurrency(contrato['currentPrices']['SELL'])
    priceLastNum = contrato['currentPrices']['LAST']
    priceLast = formatCurrency(priceLastNum)

    if priceBuy == None:
        priceBuy = ""
    if priceSell == None:
        priceSell = ""
    if priceLast == None:
        priceLast = ""
          
    priceTotal = "BUY:" + priceBuy + '/SELL:' + priceSell

    lastPnL = contrato['dbPandas'].dbGetLastPnL()
    dailyPnL = '$-.-'
    realizedPnL = '$-.-'
    unrealizedPnL = '$-.-'
    if lastPnL['dailyPnL'] != None:
        dailyPnL = formatCurrency(lastPnL['dailyPnL'])
    if lastPnL['realizedPnL'] != None:
        realizedPnL = formatCurrency(lastPnL['realizedPnL'])
    if lastPnL['unrealizedPnL'] != None:
        unrealizedPnL = formatCurrency(lastPnL['unrealizedPnL'])

    color_rojo = '#ff0000'
    color_verde = '#366b22'
    color_negro = '#000000'
    
    if estrategia == None:
        stratType = 'N/A'
        posQtyNum = None
        posQty = '0'
        execToday = 'N/A'
        execTotal = 'N/A'
        execString = 'N/A'
        totalPnl = dailyPnL + '/' + realizedPnL + '/' + unrealizedPnL
        AvgPriceFmt = 'N/A'
    else:
        stratType = estrategia['type']
        posQtyNum = estrategia['classObject'].currentPos_
        posQty = str(posQtyNum)
        execToday = estrategia['classObject'].pandas_.dbGetExecCountToday()
        execTotal = estrategia['classObject'].pandas_.dbGetExecCountAll()
        execString = str(execToday) + '/' + str(execTotal)
        allPnL = estrategia['classObject'].strategyGetExecPnL()['PnL']
        totalPnl = formatCurrency(allPnL)
        AvgPrice = estrategia['classObject'].strategyGetExecPnL()['avgPrice']
        AvgPriceFmt = formatCurrency(AvgPrice)
        try:
            unrealNum = estrategia['classObject'].strategyGetExecPnLUnrealized()
        except:
            unrealNum = 0

        unreal = formatCurrency(unrealNum)
        if unrealNum < 0:
            unreal = html.Div(unreal, style={'color':color_rojo})
        else:
            unreal = html.Div(unreal, style={'color':color_verde})

        if allPnL < 0:
            totalPnl = html.Div(totalPnl, style={'color':color_rojo})
        else:
            totalPnl = html.Div(totalPnl, style={'color':color_verde})

        #totalPnl = totalPnl + '/' + unreal
        totalPnl = html.Span(
                                [
                                    html.Div('PnL:'),
                                    html.Div(totalPnl),
                                    html.Div('/'),
                                    html.Div(unreal)
                                ], className="d-grid gap-2 d-flex justify-content-end"
                            )

    fig1 = layout_getFigureHistorico(contrato)  # de Utils
    graphColumn1 = html.Div(
        dcc.Graph(
                id={'role': 'graphDetailsStrat', 'strategy': stratType, 'symbol': symbol},
                animate = False,
                figure = fig1
        )
    )
    #, style={'color':'#ffffff','background-color':'#636363'}
    priceLastColor = color_verde
    if posQtyNum != None:
        if posQtyNum > 0:
            if priceLastNum < AvgPrice:
                priceLastColor = color_rojo
        elif posQtyNum < 0:
            if priceLastNum > AvgPrice:
                priceLastColor = color_rojo
        else:
            priceLastColor = color_negro
    else:
        priceLastColor = color_negro

    h6priceList = html.H6("("+ priceLast +")", style={'color':priceLastColor})

    this_card = dbc.Card(
        [
            dbc.CardHeader( # Lo pongo así por si luego quiero añadir cosas
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Span(
                                        [
                                            html.H6(symbol),
                                            h6priceList
                                        ], className="d-grid gap-2 d-flex"
                                    )
                                    #html.H6(symbol+" ("+ priceLast +")")
                                ],
                            )
                        ]
                    )
                ]
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div("Strategy: " + stratType, className = 'text-start', id = {'role': 'Card-Strategy', 'strategy':stratType, 'symbol': symbol}),
                                    html.Div("Pos: " + posQty, className = 'text-start', id = {'role': 'Card-Pos', 'strategy':stratType, 'symbol': symbol}),
                                ], width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Div("Executions: " + execString, className = 'text-end', id = {'role': 'Card-Executions', 'strategy':stratType, 'symbol': symbol}),
                                    html.Div(totalPnl, className = 'text-end', id = {'role': 'Card-PnL', 'strategy':stratType, 'symbol': symbol}),
                                ], width=6,
                            ),

                        ]
                    ),
                    dbc.Row(graphColumn1),
                ]
            ),
            dbc.CardFooter(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(priceTotal, className = 'text-start', id = {'role': 'Card-priceTotal', 'strategy':stratType, 'symbol': symbol})
                                ], width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Div("AvgPrice: " + AvgPriceFmt, className = 'text-end', id = {'role': 'Card-AvgPrice', 'strategy':stratType, 'symbol': symbol})
                                ], width=6,
                            )
                        ]
                    )
                ]
            ),
        ], className = 'mb-3',
    )

    return this_card


#Callback para actualizar las Cards
@callback(
    Output({'role':'summary-card', 'stratType':MATCH, 'symbol': MATCH}, "children"),
    Input({'role': 'Interval-summary-card', 'stratType':MATCH, 'symbol': MATCH}, 'n_intervals'),
    prevent_initial_call = True,
)
def actualizarCard (n_intervals):
    if not ctx.triggered_id:
        raise PreventUpdate

    symbol = ctx.triggered_id['symbol']
    stratType = ctx.triggered_id['stratType']
    logging.debug ('Actualizando card estrategia: %s', symbol)

    contract = globales.G_RTlocalData_.contractGetBySymbol(symbol)
    
    estrategia = None
    if stratType != '' and globales.G_RTlocalData_.strategies_ != None:
        estrategia = globales.G_RTlocalData_.strategies_.strategyGetStrategyBySymbolAndType (symbol, 'PentagramaRu')
    resp = create_card (contract, estrategia)

    if resp == None:
        resp = no_update

    return resp

#Callback para actualizar los precios de la cabecera
@callback(
    Output({'role':'precios_header'}, "children"),
    Input({'role':'Intervalprecios_header'}, 'n_intervals'),
    prevent_initial_call = True,
)
def actualizarPreciosTops (n_intervals):
    if not ctx.triggered_id:
        raise PreventUpdate

    resp = create_preciosTop ()

    if resp == None:
        resp = no_update

    return resp

