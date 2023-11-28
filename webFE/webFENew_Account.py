from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
from dash import html
from dash import dcc
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go 

import dash_bootstrap_components as dbc
import logging
import globales
import random

from webFE.webFENew_Utils import formatCurrencySmall

logger = logging.getLogger(__name__)
logger_root = logging.getLogger()

def layout_account_tab ():

    random_wait = random.randint(0,1000) + 10000

    fig1 = layout_getFigura()   # Lo tengo en una funcion para que sea facil actualizar
    graphColumn1 = html.Div([
        dcc.Graph(
                id={'role': 'graphAccount', 'type': 'NetLiquidation'},
                animate = False,
                figure = fig1
        ),
        dcc.Interval(
            id={'role': 'IntervalgraphAccountNet'},
            interval= random_wait, # in milliseconds
            n_intervals=0
        )
    ])
    
    tablogs = [
            dbc.Row(
                [
                    html.P("Estado Cuenta", className='text-left text-secondary mb-4 ps-0 display-6'),
                    html.Hr()
                ]
            ),
            dbc.Row
            (
                [
                    graphColumn1
                ]
            ),
    ]

    return tablogs

def layout_getFigura (update = False):

    if globales.G_RTlocalData_.accountPandas_ == None:
        return no_update

    dfAccount = globales.G_RTlocalData_.accountPandas_.dbGetAccountData()

    dfAccount = dfAccount.astype({'NetLiquidation':'float'})

    if (globales.G_RTlocalData_.accountPandas_.toPrint == False) and (update == True):
        logging.debug ('Grafico no actualizado. No hay datos nuevos')
        return no_update
   
    if len(dfAccount.index) > 0:
        LastPrice = dfAccount['NetLiquidation'][-1]
    else:
        LastPrice = 0.0

    LastPriceText = formatCurrencySmall(LastPrice, 2)
    fig2 = go.Figure()

    fig2.add_trace(
        go.Scatter(
            x=dfAccount.index, 
            y=dfAccount["NetLiquidation"], 
            mode="lines", 
            connectgaps = True, 
            name = 'NetLiquidation',
            line = dict(
                shape='spline',
                smoothing=0.5
            )
        ),
    )
    if len(dfAccount.index) > 0 and LastPrice != None:
        fig2.add_annotation(
            x = dfAccount.index[-1],
            y = LastPrice,
            text = LastPriceText,
            xshift=20,
            yshift=0,
            bordercolor='green',
            borderwidth=2,
            bgcolor="#CFECEC",
            opacity=0.8,
            showarrow=False
        )

    fig2.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
            #dict(bounds=[20.25, 15.16], pattern="hour"),  # hide hours outside of 9.30am-4pm
            #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
        ]
    )

    fig2.update_yaxes(
        tickformat='.3s',
    )

    fig2.update_layout(showlegend=False, 
                       font_size=10,
                       title_font_size=13,
                       xaxis_rangeslider_visible=False, 
                       yaxis={'side': 'right'} ,
                       title_text='NetLiquidation', 
                       title_x = 0.5,
                       title_xanchor = 'center',
                       margin=dict(l=0, r=0, t=40, b=40),
                       hovermode="x unified")

    globales.G_RTlocalData_.accountPandas_.toPrint = False

    return fig2

#Callback para actualizar grafica today
@callback(
    Output({'role': 'graphAccount', 'type': 'NetLiquidation'}, 'figure'),
    Input({'role': 'IntervalgraphAccountNet'}, 'n_intervals'),
    prevent_initial_call = True,
)
def actualizarFiguraAccount (n_intervals):
    if not ctx.triggered_id:
        raise PreventUpdate

    fig1 = layout_getFigura (True)

    #return  zonasFilaBorderDown, no_update, no_update
    return  fig1