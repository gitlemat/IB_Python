from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback, DiskcacheManager
from dash import html
from dash import dcc
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go 
import random
import string
import datetime

import dash_bootstrap_components as dbc
import logging
import globales
import math_utils
import utils

logger = logging.getLogger(__name__)
logger_root = logging.getLogger()

def layout_contractView_tab ():

    contract_view_list = {}
    contract_view_list['HE'] = ['HEM-2HEN+HEQ', 'HEZ-2HEG+HEJ']
    contract_view_list['LE'] = ['LEM-2LEN+LEQ', 'LEM-2LEQ+LEV', 'LEZ-2LEG+LEJ', 'LEJ-2LEM+LEQ', 'LEZ-2LEG+LEJ']
    contract_view_list['ZL'] = ['ZLN-2ZLZ+ZLN', 'ZLN-2ZLQ+ZLU']
    contract_view_list['CC'] = ['CCZ-2CCH+CCK', 'CCH-2CCK+CCN', 'CCN-2CCU+CCZ', 'CCU-2CCZ+CCH']
    contract_view_list['HO'] = ['HOH-2HOJ+HOK']
    contract_view_list['GF'] = ['GFJ-2GFK+GFQ', 'GFQ-2GFU+GFV']
    contract_view_list['CL'] = ['CLQ-2CLV+CLZ', 'CLZ-2CLH+CLN', 'CLZ-2CLH+CLZ', 'CLF-2CLG+CLH', 'CLM-2CLZ+CLM', 'CLX-2CLZ+CLF', 'CLU-2CLV+CLX']
    contract_view_list['NG'] = ['NGV-2NGX+NGZ','NGZ-2NGF+NGG','NGM-2NGN+NGQ','NGX-2NGZ+NGF']
    contract_view_list['RB'] = ['RBH-2RBJ+RBK']
    contract_view_list['ZM'] = ['ZMH-2ZMK+ZMN','ZMQ-2ZMV+ZMZ']
    contract_view_list['ZS'] = ['ZSH-2ZSK+ZSN']
    contract_view_list['ZC'] = ['ZCN-2ZCU+ZCZ', 'ZCK-2ZCN+ZCU']
    contract_view_list['ZW'] = ['ZWZ-2ZWH+ZWK', 'ZWH-2ZWN+ZWZ']

    cardNumber = 0
    nColumns = 4
    lenCol = int (12/nColumns)
    stacks = []
    for n in range (nColumns):
        stacks.append([])

    listGraphCards = []

    for family_code in contract_view_list:
        this_card = createContractOnOffCard (family_code, contract_view_list)
        colStack = cardNumber % nColumns
        stacks[colStack].append(this_card)
        for code in contract_view_list[family_code]:
            logging.debug ('%s -> %s', family_code, code)
            this_graghCard = createGraphCard (code, family_code)
            listGraphCards.append(this_graghCard)
        cardNumber += 1

    allColumns = []
    for n in range (nColumns):
        columna = dbc.Col([
            dbc.Stack(stacks[n])
        ], width=lenCol)
        allColumns.append(columna)

    tabContractView = [
        dbc.Row(
            [

                dbc.Col(
                    html.P("Analisis Contratos", className='text-left mb-0 text-secondary display-6'),
                    className = 'ps-0',
                    width = 9
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
            allColumns,
        ),
        dbc.Row(
            [
                dbc.Progress(value = 0, id = {'role': 'progress-bar'}, style= {'visibility': 'hidden'}),
            ]
        ),
        dbc.Row(
            [
                html.Hr()
            ]
        ),
        dbc.Row(
            listGraphCards, id={'role': 'cajasGraphs'}
        ),
    ]

    return tabContractView

def createContractOnOffCard (family_code, contract_view_list):

    labelName = utils.code2name(family_code) + ' (' + family_code + ')'
    bodyContent = []
    for spread in contract_view_list[family_code]:
        bodyContent.append(html.P(spread, className='text9-7 mb-0'))

    symbols = ','.join(contract_view_list[family_code])

    this_card = dbc.Card(
        [
            dbc.CardHeader(
                [
                    dbc.Checkbox(
                        id = {'role': 'caja_onoff', 'symbol_family': family_code, 'symbols': symbols},
                        label=labelName,
                        value=False,
                        label_class_name='text9-7 mb-0'
                    ),
                    
                ], className = 'pt-0 pb-0',
            ),
            dbc.CardBody( # Lo pongo así por si luego quiero añadir cosas
                bodyContent,
                className = 'pt-0 pb-0',
            )
        ], 
        className = 'mb-3 ps-0 pe-0',
    )

    return this_card

def createGraphCard (code = None, family_code = None):
    this_card = dbc.Card(
        [], 
        className = 'ps-0',  # className = 'mb-3 ps-0 pe-0', 
        style= {'display': 'none'},
        id = {'role': 'card_graph', 'symbol_family': family_code, 'symbol': code}
    )
    return this_card

def createGraphCardContent (code = None):

    try:
        if code == None:
            logging.error ('El codigo de la familia es NULL')
            return no_update
    except:
        pass

    dataFamilies_ = globales.G_RTlocalData_.contractListPandas_.Families_

    if code not in dataFamilies_:
        logging.error ('El codigo (%s) no esta en la db', code)
        return no_update
    
    symbols = dataFamilies_[code]['symbols']
    last_year = dataFamilies_[code]['lastYear']
    symbols = utils.codesFromYear(symbols, int(last_year) - 6)

    fig2 = go.Figure()

    stopDateRef = None # tomamos la del pimero para poder dibujar correctamente

    for symbol in symbols:
        # Primero leemos la fecha de cada simbolo
        symbolStart, symbolStop = globales.G_RTlocalData_.contractListPandas_.influxIC_.influxGetFirstLastRecordsDataFrame(symbol)

        if symbolStart == None or symbolStop == None:
            logging.error ('Resultado de fechas vacio')
            continue
        
        symbolStart = utils.dateLocal2UTC (symbolStart)
        symbolStop = utils.dateLocal2UTC (symbolStop)
        logging.info('Symbol: %s', symbol)
        logging.info('Start Date: %s', symbolStart)
        logging.info('End Date: %s', symbolStop)
    
        symbolStart = symbolStop - datetime.timedelta(days=485) # 16 meses

        if stopDateRef == None:
            stopDateRef = symbolStop

        yearsDelta = symbolStop - stopDateRef

        try:
            df1_ = globales.G_RTlocalData_.contractListPandas_.influxIC_.influxGetCloseValueDataFrame (symbol, symbolStart, symbolStop)
            df1_.index = df1_.index - yearsDelta
        except:
            logging.error ('Error obteniendo datos para %s', symbol)
            continue

        linel = dict(shape='spline', smoothing=0.5)
        fig2.add_trace(
            go.Scatter(
                x=df1_.index, 
                y=df1_['close'], 
                mode="lines", 
                connectgaps = True, 
                name = symbol,
                line = linel
            ),
        )

    fig2.update_layout(showlegend=True, 
                       font_size=10,
                       title_font_size=13,
                       xaxis_rangeslider_visible=False, 
                       yaxis={'side': 'left'} ,
                       title_text= "\"" + code + "\"" ' Stacked', 
                       title_x = 0.5,
                       title_xanchor = 'center',
                       legend_x=0, legend_y=1,
                       margin=dict(l=0, r=0, t=40, b=40),
                       hovermode="x unified")
    
    graphColumn1 = html.Div([
        dcc.Graph(
                animate = False,
                figure = fig2
        )
    ])
    
    this_card_content = [
        dbc.CardBody( # Lo pongo así por si luego quiero añadir cosas
            graphColumn1,
            className = 'pt-0 pb-0',
        )
    ]
    return this_card_content

# Callback para añadir graph
@callback(
    Output({'role': 'card_graph', 'symbol_family': MATCH, 'symbol': ALL}, component_property='style'),
    Output({'role': 'card_graph', 'symbol_family': MATCH, 'symbol': ALL}, "children"),
    Output({'role': 'card_graph', 'symbol_family': MATCH, 'symbol': ALL}, component_property='className'),
    Input({'role': 'caja_onoff', 'symbol_family': MATCH, 'symbols': ALL}, "value"),
    Input({'role': 'card_graph', 'symbol_family': MATCH, 'symbol': ALL}, component_property='className'),
    background=True,
    running=[
        (
            Output({'role': 'progress-bar'}, "style"),
            {"visibility": "visible"},
            {"visibility": "hidden"},
        )
    ],
    progress=[
        Output({'role': 'progress-bar'}, "value"), 
        Output({'role': 'progress-bar'}, "max")
    ],
    prevent_initial_call = True,
)
def addCardGraphCode(set_progress, value_onoff, className):
    # Esto es por si las moscas
    if not ctx.triggered_id:
        raise PreventUpdate
    if ctx.triggered_id['role'] != 'caja_onoff':
        raise PreventUpdate

    symbols = ctx.triggered_id['symbols'].split(',')
    nLen = len(symbols)
    logging.info ('Id: %s. Value: %s. symbols: %s, className: %s', ctx.triggered_id, value_onoff, symbols, className)

    visibility_state = {'display': 'block'}
    new_class = 'ps-0'
    if value_onoff[0] == True:
        visibility_state = {'display': 'block'}
    if value_onoff[0] == False:
        visibility_state = {'display': 'none'}

    res_visibility = []
    new_cajas = []
    new_classes = []
    dataFamilies_ = globales.G_RTlocalData_.contractListPandas_.Families_

    set_progress(('0', '1')) # Para resetear la barra

    # Identifico cuantos elementos se calculan para el tema de la barra de progreso
    nElements = 0
    for nIter in range (nLen):
        if className[nIter] == 'ps-0' and value_onoff[0] == True:
            code = symbols[nIter]
            if code not in dataFamilies_:
                continue
            symbols_de_mariposa = dataFamilies_[code]['symbols']
            last_year = dataFamilies_[code]['lastYear']
            symbols_de_mariposa = utils.codesFromYear(symbols_de_mariposa, int(last_year) - 6)
            nElements += len (symbols_de_mariposa)
            logging.debug('nElements: \n%s', symbols_de_mariposa)

    # Ahora lo hacemos de verdad
    nProgress = 0
    for nIter in range (nLen):
        if className[nIter] == 'ps-0' and value_onoff[0] == True:
            #new_caja = createGraphCardContent (code = symbols[nIter])

            code = symbols[nIter]
            if code not in dataFamilies_:
                logging.error ('El codigo (%s) no esta en la db', code)
                res_visibility.append(visibility_state)
                new_cajas.append(no_update)
                new_classes.append(new_class)
                continue
            
            symbols_de_mariposa = dataFamilies_[code]['symbols']
            last_year = dataFamilies_[code]['lastYear']
            symbols_de_mariposa = utils.codesFromYear(symbols_de_mariposa, int(last_year) - 6)
        
            fig2 = go.Figure()
        
            stopDateRef = None # tomamos la del pimero para poder dibujar correctamente

            last2symbols = utils.last2yearsFromFamily(symbol)
        
            for symbol in symbols_de_mariposa:
                # Primero leemos la fecha de cada simbolo
                nProgress += 1
                symbolStart, symbolStop = globales.G_RTlocalData_.contractListPandas_.influxIC_.influxGetFirstLastRecordsDataFrame(symbol)
        
                if symbolStart == None or symbolStop == None:
                    logging.error ('Resultado de fechas vacio')
                    set_progress((str(nProgress), str(nElements)))
                    continue
                
                symbolStart = utils.dateLocal2UTC (symbolStart)
                symbolStop = utils.dateLocal2UTC (symbolStop)
                logging.info('Symbol: %s', symbol)
                logging.info('Start Date: %s', symbolStart)
                logging.info('End Date: %s', symbolStop)
            
                symbolStart = symbolStop - datetime.timedelta(days=485) # 16 meses
        
                if stopDateRef == None:
                    stopDateRef = symbolStop
        
                yearsDelta = symbolStop - stopDateRef
        
                try:
                    df1_ = globales.G_RTlocalData_.contractListPandas_.influxIC_.influxGetCloseValueDataFrame (symbol, symbolStart, symbolStop)
                    df1_.index = df1_.index - yearsDelta
                except:
                    logging.error ('Error obteniendo datos para %s', symbol)
                    set_progress((str(nProgress), str(nElements)))
                    continue
        
                if symbol in last2symbols:
                    linel = dict(color='rgb(0,0,0)', width=4, dash='dash', shape='spline', smoothing=0.5)
                else:
                    linel = dict(shape='spline', smoothing=0.5)
                fig2.add_trace(
                    go.Scatter(
                        x=df1_.index, 
                        y=df1_['close'], 
                        mode="lines", 
                        connectgaps = True, 
                        name = symbol,
                        line = linel
                    ),
                )
                set_progress((str(nProgress), str(nElements)))
                logging.info ('Progreso %s/%s', str(nProgress), str(nElements))
        
            fig2.update_layout(showlegend=True, 
                               font_size=10,
                               title_font_size=13,
                               xaxis_rangeslider_visible=False, 
                               yaxis={'side': 'left'} ,
                               title_text= "\"" + code + "\"" ' Stacked', 
                               title_x = 0.5,
                               title_xanchor = 'center',
                               legend_x=0, legend_y=1,
                               margin=dict(l=0, r=0, t=40, b=40),
                               hovermode="x unified")
            
            graphColumn1 = html.Div([
                dcc.Graph(
                        animate = False,
                        figure = fig2
                )
            ])
            
            new_caja = [
                dbc.CardBody( # Lo pongo así por si luego quiero añadir cosas
                    graphColumn1,
                    className = 'pt-0 pb-0',
                )
            ]

            if new_caja == no_update:
                new_class = no_update
            else:
                new_class = 'mb-3 ps-0 pe-0'
        else:
            new_caja = no_update
            new_class = no_update
        
        new_cajas.append(new_caja)
        res_visibility.append(visibility_state)
        new_classes.append(new_class)
        

    logging.info ('res: %s. new_calsees: %s', res_visibility, new_classes)
    return res_visibility, new_cajas, new_classes
