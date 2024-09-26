from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
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


from webFE.webFENew_Utils import formatCurrencySmall

logger = logging.getLogger(__name__)
logger_root = logging.getLogger()

def layout_math_tab ():
    
    box = []
    box.append(createSpreadStackGraphBox())   
    box.append(createMaxCrossGraphBox())

    tabMath = [
        dbc.Row(
            [

                dbc.Col(
                    html.P("Pruebas de Calculos", className='text-left mb-0 text-secondary display-6'),
                    className = 'ps-0',
                    width = 9
                ),
                dbc.Col(
                    html.Div(
                        dbc.Button("Añadir Caja", id={'role': 'AddBox'}, className="text9-7 me-0", n_clicks=0),
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
            box, id = {'role': 'cajas_math'}
        ),
    ]

    return tabMath

def createSpreadStackGraphBox ():

    dataFamilies_ = globales.G_RTlocalData_.contractListPandas_.Families_
    datal_ = globales.G_RTlocalData_.contractListPandas_.Contracts_
    cl_ = []
    fl_ = []

    # Solo pillamos las mariposas (longitud 3)
    for code in datal_:
        if code['nLegs'] == 3:
            cl_.append(code['symbol'])
    for family in dataFamilies_:
        if dataFamilies_[family]['nLegs'] == 3:
            fl_.append(family)

    cl_.sort()

    #familyList_ = getSpreadFamiliesFromList (cl_)

    characters = string.ascii_letters + string.digits
    uuid = ''.join(random.choice(characters) for i in range(16))

    box1 = dcc.Dropdown(fl_, multi=False, id={'role': 'select_codes_stack', 'uuid': uuid})
    buttonPresentar = dbc.Button("Presentar", id={'role': 'BotonStackPresent', 'uuid': uuid}, className="text9-7 me-2", n_clicks=0)

    fig1 = layout_getFiguraStack()   # Lo tengo en una funcion para que sea facil actualizar
    graphColumn1 = html.Div([
        dcc.Graph(
                id={'role': 'graphSpreadStack', 'uuid': uuid},
                animate = False,
                figure = fig1
        )
    ])

    this_card = dbc.Card(
        [
            dbc.CardBody( # Lo pongo así por si luego quiero añadir cosas
                [
                    dbc.Row(
                        [
                            graphColumn1
                        ], className = 'mb-3'
                    ),
                    dbc.Row
                    (
                        [
                            dbc.Col(box1),
                        ], className = 'mb-3',
                    ),
                    dbc.Row
                    (
                        [
                            dbc.Col(buttonPresentar, width=6),
                        ]
                    ),
                ]
            )
        ], className = 'mb-3'
    )

    return this_card

def createMaxCrossGraphBox ():

    dataFamilies_ = globales.G_RTlocalData_.contractListPandas_.Families_
    datal_ = globales.G_RTlocalData_.contractListPandas_.Contracts_
    cl_ = []
    fl_ = []

    for code in datal_:
        if code['nLegs'] == 3:
            cl_.append(code['symbol'])
    for family in dataFamilies_:
        if dataFamilies_[family]['nLegs'] == 3:
            fl_.append(family)

    cl_.sort()
    fl_.sort()

    characters = string.ascii_letters + string.digits
    uuid = ''.join(random.choice(characters) for i in range(16))

    box1 = dcc.Dropdown(fl_+cl_, multi=True, id={'role': 'select_codes_cross', 'uuid': uuid})
    distancia = dbc.Input(placeholder="Distancia (%.%)", type="number", id={'role': 'distancia', 'uuid': uuid}, min=0, max=100)
    delta_init = dbc.Input(placeholder="Delta Init (dias)", type="number", id={'role': 'delta_init', 'uuid': uuid}, min=0, max=1000)
    delta_end = dbc.Input(placeholder="Delta End (dias)", type="number", id={'role': 'delta_end', 'uuid': uuid}, min=0, max=1000)
    distanciaTip = dbc.Tooltip("Distancia minima para considerar el corte",target={'role': 'distancia', 'uuid': uuid})
    delta_initTip = dbc.Tooltip("Dias que no contamos al inicio",target={'role': 'delta_init', 'uuid': uuid})
    delta_endTip = dbc.Tooltip("Dias que no contamos al final",target={'role': 'delta_end', 'uuid': uuid})
    buttonCalcularMaxCross = dbc.Button("MaxCross", id={'role': 'MaxCrossButton', 'uuid': uuid}, className="text9-7 me-2", n_clicks=0)

    fig1 = layout_getFigura()   # Lo tengo en una funcion para que sea facil actualizar
    graphColumn1 = html.Div([
        dcc.Graph(
                id={'role': 'graphMaxCorss', 'uuid': uuid},
                animate = False,
                figure = fig1
        )
    ])

    this_card = dbc.Card(
        [
            dbc.CardBody( # Lo pongo así por si luego quiero añadir cosas
                [
                    dbc.Row(
                        [
                            graphColumn1
                        ], className = 'mb-3'
                    ),
                    dbc.Row
                    (
                        [
                            dbc.Col(box1),
                        ], className = 'mb-3',
                    ),
                    dbc.Row
                    (
                        [
                            dbc.Col(buttonCalcularMaxCross, width=6),
                            dbc.Col([distancia, distanciaTip], width=2),
                            dbc.Col([delta_init, delta_initTip], width=2),
                            dbc.Col([delta_end, delta_endTip], width=2),
                        ]
                    ),
                ]
            )
        ], className = 'mb-3'
    )

    return this_card 

def layout_getFiguraStack (code = None, update = False):

    try:
        if code == None:
            return no_update
    except:
        pass

    dataFamilies_ = globales.G_RTlocalData_.contractListPandas_.Families_

    if code not in dataFamilies_:
        return no_update
    
    symbols = dataFamilies_[code]['symbols']

    fig2 = go.Figure()

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

    stopDateRef = None # tomamos la del pimero para poder dibujar correctamente

    for symbol in symbols:
        # Primero leemos la fecha de cada simbolo
        symbolStart, symbolStop = globales.G_RTlocalData_.contractListPandas_.influxIC_.influxGetFirstLastRecordsDataFrame(symbol)

        if symbolStart == None or symbolStop == None:
            logging.error ('Resultado de fechas vacio')
            return fig2
        
        symbolStart = utils.dateLocal2UTC (symbolStart)
        symbolStop = utils.dateLocal2UTC (symbolStop)
        logging.debug('Symbol: %s', symbol)
        logging.debug('Start Date: %s', symbolStart)
        logging.debug('End Date: %s', symbolStop)
    
        symbolStart = symbolStop - datetime.timedelta(days=485) # 16 meses

        if stopDateRef == None:
            stopDateRef = symbolStop

        yearsDelta = symbolStop - stopDateRef

        df1_ = globales.G_RTlocalData_.contractListPandas_.influxIC_.influxGetCloseValueDataFrame (symbol, symbolStart, symbolStop)
        df1_.index = df1_.index - yearsDelta

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

    

    return fig2

def layout_getFigura (datos_df = None, update = False):

    try:
        if datos_df == None:
            return no_update
    except:
        pass
    
    fig2 = go.Figure()

    for symbol in datos_df:
        if symbol == 'media':
            linel = dict(color='rgb(0,0,0)', width=4, dash='dash', shape='spline', smoothing=0.5)
        else:
            linel = dict(shape='spline', smoothing=0.5)
        fig2.add_trace(
            go.Scatter(
                x=datos_df.index, 
                y=datos_df[symbol], 
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
                       title_text='CrossMax', 
                       title_x = 0.5,
                       title_xanchor = 'center',
                       legend_x=0, legend_y=1,
                       margin=dict(l=0, r=0, t=40, b=40),
                       hovermode="x unified")

    return fig2

def rangeFromSymbol (symbol):
    code_decomp = utils.contractCode2list(symbol)

    pos = 0
    yearSymbol = '24'
    monthSymbol = '01'
    daySymbol = '28'
    for codeDict in code_decomp:
        pos += 1
        code = codeDict['code']
        if pos == len (code_decomp):
            while code[-1].isnumeric():
                code = code[:-1]
            monthSymbol = code[-1]
            yearSymbol = codeDict['code'][len(code):]

    monthSymbol = utils.letter2Month(monthSymbol)
            
    yearSymbol =  daySymbol + '/' + monthSymbol + '/' + '20' + yearSymbol
    symbolStop = datetime.datetime.strptime(yearSymbol, "%d/%m/%Y")
    symbolStart = symbolStop - datetime.timedelta(days=485) # 16 meses

    logging.info('Symbol: %s', symbol)
    logging.info('Start Date: %s', symbolStart)
    logging.info('End Date: %s', symbolStop)

    return symbolStart, symbolStop


# Callback para cargar MaxCross
@callback(
    Output({'role': 'graphMaxCorss', 'uuid': MATCH}, "figure"),
    Input({'role': 'select_codes_cross', 'uuid': MATCH}, "value"),
    Input({'role': 'distancia', 'uuid': MATCH}, "value"),
    Input({'role': 'delta_init', 'uuid': MATCH}, "value"),
    Input({'role': 'delta_end', 'uuid': MATCH}, "value"),
    Input({'role': 'MaxCrossButton', 'uuid': ALL}, "n_clicks"),
    prevent_initial_call = True,
)
def maxCrossValues(codes, distancia, delta_init, delta_end, n_button):
        # Esto es por si las moscas
    if not ctx.triggered_id or n_button == None:
        raise PreventUpdate
    
    logging.info ('Id: %s', ctx.triggered_id)
        
    if ctx.triggered_id['role'] != 'MaxCrossButton':
        raise PreventUpdate

    logging.info ('Id: %s', ctx.triggered_id)

    if distancia == None:
        distancia = 0

    params = {
        'distancia': distancia,
        'delta_init':delta_init,
        'delta_end':delta_end
    }

    esodf = math_utils.calcular_best_media_symbols (codes, params)

    logging.debug ('Crossing:\n%s', esodf)

    fig1 = layout_getFigura(esodf)

    return fig1

# Callback para cargar StackFig
@callback(
    Output({'role': 'graphSpreadStack', 'uuid': MATCH}, "figure"),
    Input({'role': 'select_codes_stack', 'uuid': MATCH}, "value"),
    Input({'role': 'BotonStackPresent', 'uuid': ALL}, "n_clicks"),
    prevent_initial_call = True,
)
def stackValuesFig(codes, n_button):
        # Esto es por si las moscas
    if not ctx.triggered_id or n_button == None:
        raise PreventUpdate
            
    if ctx.triggered_id['role'] != 'BotonStackPresent':
        raise PreventUpdate

    logging.info ('Id: %s', ctx.triggered_id)
    logging.info ('Code: %s', codes)

    fig1 = layout_getFiguraStack(codes)

    return fig1

# Callback para añadir caja
@callback(
    Output({'role': 'cajas_math'}, "children"),
    Input({'role': 'cajas_math'}, "children"),
    Input({'role': 'AddBox'}, "n_clicks"),
    prevent_initial_call = True,
)
def addBoxes(currentBoxes, n_button):
        # Esto es por si las moscas
    if not ctx.triggered_id:
        raise PreventUpdate
        
    if ctx.triggered_id['role'] != 'AddBox':
        raise PreventUpdate

    logging.info ('Id: %s', ctx.triggered_id)

    newbox = createMaxCrossGraphBox()

    currentBoxes.append(newbox)

    return currentBoxes

