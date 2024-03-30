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

    tabSummary = [
        dbc.Row(
            [
                html.P("Resumen Global", className='text-left text-secondary mb-4 ps-0 display-6'),
                html.Hr()
            ]
        ),
    ]

    contractList = globales.G_RTlocalData_.contratoReturnDictAll()
    if globales.G_RTlocalData_.strategies_ == None:
        return tabSummary
        
    strategyList = globales.G_RTlocalData_.strategies_.strategyGetAll()

    dfAccount = globales.G_RTlocalData_.accountPandas_.dbGetAccountData()
    dfAccount = dfAccount.astype({'NetLiquidation':'float'})

    try:
        LastNetLiq1 = dfAccount.iloc[-1]['NetLiquidation']
    except:
        LastNetLiq1 = 0.0

    try:
        LastNetLiq2 = dfAccount.iloc[-2]['NetLiquidation']
    except:
        LastNetLiq2 = 0.0

    if LastNetLiq2 != 0:
        increment = (LastNetLiq1 - LastNetLiq1) / LastNetLiq2 * 100
    else:
        increment = 0

    logging.info ('NetLiq:\n%s\n%s\n%s', LastNetLiq1, LastNetLiq2, increment)
    
    all_cards = []
    included_contracts = []
    for estrategia in strategyList:
        symbol = estrategia['symbol']
                
        contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
        if not contrato:
            logging.error ('Error cargando estrategia Headerde %s. No tenemos el contrato cargado en RT_Data', symbol)
            return no_update

        included_contracts.append(symbol)

        #fig1 = webFE.webFENew_Strategies.layout_getFigura1(estrategia)
        fig1 = layout_getFigureHistorico(contrato)  # de Utils

        this_card = create_card (contrato, fig1, estrategia)

        all_cards.append(this_card)

    for gConId, contrato in contractList.items():
        indirect = globales.G_RTlocalData_.contractIndirectoGet (gConId) # Podria leer de contrato, pero es una guarregria (como mucho de lo que hay aqui)
        logging.debug ('Contrato Indirecto %s', indirect)
        if indirect:
            continue
        symbol = contrato['fullSymbol']

        if symbol in included_contracts:
            continue

        #fig1 = webFE.webFENew_Contratos.getFiguraComp(contrato)
        fig1 = layout_getFigureHistorico(contrato)  # de Utils

        this_card = create_card (contrato, fig1, None)

        all_cards.append(this_card)

    # Ahora añadimos la lista de execs a tabSummary

    df_execs = globales.G_RTlocalData_.strategies_.strategyGetAllExecs()

    if len(df_execs) > 0:
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
        column1 = dbc.Col(all_cards[i], id='summary-card-l-'+str(i), md=6)
        column2 = None
        if i + 1 < len(all_cards):
            column2 = dbc.Col(all_cards[i+1], id='summary-card-r-'+str(i+1), md=6)
        
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

def create_card (contrato, fig1, estrategia):
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
    dailyPnL = ''
    realizedPnL = ''
    unrealizedPnL = ''
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
        posQty = 'N/A'
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
        unrealNum = estrategia['classObject'].strategyGetExecPnLUnrealized()
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

