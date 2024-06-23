from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
from dash import html
from dash import dcc
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go 
import random
import string

import dash_bootstrap_components as dbc
import logging
import globales
import math_utils


from webFE.webFENew_Utils import formatCurrencySmall

logger = logging.getLogger(__name__)
logger_root = logging.getLogger()

def layout_math_tab ():
    
    box = []
    box.append(createGraphBox())

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

def createGraphBox ():

    datal_ = globales.G_RTlocalData_.contractListPandas_.Contracts_
    cl_ = []

    for code in datal_:
        if code['nLegs'] == 3:
            cl_.append(code['symbol'])

    cl_.sort()

    characters = string.ascii_letters + string.digits
    uuid = ''.join(random.choice(characters) for i in range(16))

    box1 = dcc.Dropdown(cl_, multi=True, id={'role': 'select_codes', 'uuid': uuid})
    distancia = dbc.Input(type="number", id={'role': 'distancia', 'uuid': uuid}, min=0, max=100)
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
            dbc.CardHeader( # Lo pongo así por si luego quiero añadir cosas
                [
                    dbc.Row(
                        [
                            graphColumn1
                        ], className = 'mb-3'
                    ),
                    dbc.Row
                    (
                        [
                            dbc.Col(box1, width=9),
                            dbc.Col(distancia, width=3),
                        ], className = 'mb-3',
                    ),
                    dbc.Row
                    (
                        [
                            dbc.Col(buttonCalcularMaxCross),
                        ]
                    ),
                ]
            )
        ], className = 'mb-3'
    )

    return this_card

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

# Callback para cargar MaxCross
@callback(
    Output({'role': 'graphMaxCorss', 'uuid': MATCH}, "figure"),
    Input({'role': 'select_codes', 'uuid': MATCH}, "value"),
    Input({'role': 'distancia', 'uuid': MATCH}, "value"),
    Input({'role': 'MaxCrossButton', 'uuid': ALL}, "n_clicks"),
    prevent_initial_call = True,
)
def maxCrossValues(codes, distancia, n_button):
        # Esto es por si las moscas
    if not ctx.triggered_id or n_button == None:
        raise PreventUpdate
        
    if ctx.triggered_id['role'] != 'MaxCrossButton':
        raise PreventUpdate

    logging.info ('Id: %s', ctx.triggered_id)

    if distancia == None:
        distancia = 0

    esodf = math_utils.calcular_best_media_symbols (codes, distancia)

    logging.debug ('Crossing:\n%s', esodf)

    fig1 = layout_getFigura(esodf)

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

    newbox = createGraphBox()

    currentBoxes.append(newbox)

    return currentBoxes

