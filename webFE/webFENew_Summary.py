import webFE.webFENew_Strategies
import webFE.webFENew_Contratos


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

def layout_summary_tab ():
    contractList = globales.G_RTlocalData_.contratoReturnDictAll()
    strategyList = globales.G_RTlocalData_.strategies_.strategyGetAll()
    tabSummary = [
        dbc.Row(
            [
                html.P("Resumen Global", className='text-left text-secondary mb-4 ps-0 display-6'),
                html.Hr()
            ]
        ),
    ]
    
    all_cards = []
    included_contracts = []
    for estrategia in strategyList:
        symbol = estrategia['symbol']
        
        contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
        if not contrato:
            logging.error ('Error cargando estrategia Headerde %s. No tenemos el contrato cargado en RT_Data', symbol)
            return no_update

        included_contracts.append(symbol)

        fig1 = webFE.webFENew_Strategies.layout_getFigura1(estrategia)

        this_card = create_card (contrato, fig1, estrategia)

        all_cards.append(this_card)

    for gConId, contrato in contractList.items():
        indirect = globales.G_RTlocalData_.contractIndirectoGet (gConId) # Podria leer de contrato, pero es una guarregria (como mucho de lo que hay aqui)
        logging.info ('Contrato Indirecto $s', indirect)
        if indirect:
            continue
        symbol = contrato['fullSymbol']

        if symbol in included_contracts:
            continue

        fig1 = webFE.webFENew_Contratos.getFiguraComp(contrato)

        this_card = create_card (contrato, fig1, None)

        all_cards.append(this_card)

    '''
    row_complete = True
    for a_card in all_cards:
        if row_complete:
            a_row = []
        column = dbc.Col(a_card, width=6)
        a_row.append(column)

        if not row_complete:
            row_complete = True
            row = dbc.Row(a_row)
            tabSummary.append(row)
    '''

    for i in range(0, len(all_cards), 2):
        logging.info ('Card: %d, %d', i, len(all_cards))
        column1 = dbc.Col(all_cards[i], width=6)
        column2 = None
        if i + 1 < len(all_cards):
            column2 = dbc.Col(all_cards[i+1], width=6)
        
        row = dbc.Row(
            [
                column1,
                column2,
            ]
        )  
        tabSummary.append(row)




        

    return tabSummary

def create_card (contrato, fig1, estrategia):
    symbol = contrato['fullSymbol']
    priceBuy = formatCurrency(contrato['currentPrices']['BUY'])
    priceSell = formatCurrency(contrato['currentPrices']['SELL'])
    priceLast = formatCurrency(contrato['currentPrices']['LAST'])
    priceTotal = "BUY:" + priceBuy + '/SELL:' + priceSell + '/LAST:' + priceLast

    if estrategia == None:
        stratType = 'N/A'
        posQty = 'N/A'
        execToday = 'N/A'
        execTotal = 'N/A'
        execString = 'N/A'
    else:
        stratType = estrategia['type']
        posQty = str(estrategia['classObject'].currentPos_)
        execToday = estrategia['classObject'].pandas_.dbGetExecCountToday()
        execTotal = estrategia['classObject'].pandas_.dbGetExecCountAll()
        execString = str(execToday) + '/' + str(execTotal)

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
    totalPnl = dailyPnL + '/' + realizedPnL + '/' + unrealizedPnL

    graphColumn1 = html.Div(
        dcc.Graph(
                id={'role': 'graphDetailsStrat', 'strategy': stratType, 'symbol': symbol},
                animate = False,
                figure = fig1
        )
    )

    this_card = dbc.Card(
        [
            dbc.CardHeader(html.H4(symbol)),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div("Strategy: " + stratType, className = 'text-start'),
                                    html.Div("Pos: " + posQty, className = 'text-start'),
                                ], width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Div("Executions: " + execString, className = 'text-end'),
                                    html.Div("PnL: " + totalPnl, className = 'text-end'),
                                ], width=6,
                            ),

                        ]
                    ),
                    dbc.Row(graphColumn1),
                ]
            ),
            dbc.CardFooter(priceTotal),
        ], className = 'mb-3',
    )

    return this_card

