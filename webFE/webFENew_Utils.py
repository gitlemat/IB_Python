import logging
import globales
import plotly.graph_objects as go
from plotly.subplots import make_subplots


logger = logging.getLogger(__name__)


#####################################################################################################################
#####################################################################################################################
## Utils

def formatCurrency (cantidad):
    thousands_separator = "."
    fractional_separator = ","
    
    try:
        currency = "${:,.2f}".format(cantidad)
    except:
        logging.error ('La cantidad de dinero no es correcta')
        return None
    
    if thousands_separator == ".":
        if '.' in currency:
            main_currency, fractional_currency = currency.split(".")[0], currency.split(".")[1]
        else:
            main_currency = currency
        new_main_currency = main_currency.replace(",", ".")
        if '.' in currency:
            currency = new_main_currency + fractional_separator + fractional_currency
        else:
            currency = new_main_currency
    
    return (currency)

def layout_getFigureHistorico (contrato):

    fig1 = go.Figure()
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])

    if contrato['dbPandas']:
        df_comp = contrato['dbPandas'].dbGetDataframeComp()
        df_vol = contrato['dbPandas'].dbGetDataframeVolume()
        #logging.info('\n%s', df_vol)
        LastPrice = contrato['dbPandas'].dbGetLastPrices()['LAST']
        if not LastPrice:
            if  len(df_comp)>0:
                LastPrice = df_comp['close'][-1]
            else:
                LastPrice = 0.0

        fig1.add_trace(
            go.Bar(
                x=df_vol.index, 
                y=df_vol['Volume'],
                marker_color='rgb(255, 190, 190)'
            ),
            secondary_y=False
        )
        
        fig1.add_trace(
            go.Candlestick(
                x=df_comp.index, 
                open=df_comp['open'], 
                high=df_comp['high'],
                low=df_comp['low'],
                close=df_comp['close']
            ),
            secondary_y=True
        )

        if len(df_comp.index) > 0:
            fig1.add_annotation(
                x = df_comp.index[-1],
                y = LastPrice,
                text = f"{LastPrice:0.2f}",
                xshift=20,
                yshift=0,
                bordercolor='green',
                borderwidth=2,
                bgcolor="#CFECEC",
                opacity=0.8,
                showarrow=False, 
                yref="y2"
            )

    
    fig1.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
            dict(bounds=[21.1, 15], pattern="hour"),  # hide hours outside of 9.30am-4pm
            #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
        ]
    )
    fig1.update_yaxes(
        tickformat='.2f', 
        secondary_y=True
    )

    fig1.layout.yaxis.showgrid=False
    fig1.layout.yaxis2.showgrid=False

    fig1.update_layout(showlegend=False, 
                       xaxis_rangeslider_visible=False, 
                       yaxis={'side': 'left'} ,
                       yaxis2={'side': 'right'} ,
                       title_text='Historico', 
                       title_x = 0.5,
                       title_xanchor = 'center',
                       margin=dict(l=10, r=10, t=40, b=40),
                       hovermode="x unified"
    )

    return fig1


















