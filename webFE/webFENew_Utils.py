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

def formatCurrencySmall (cantidad, digits_integer):
    try:
        cantidad = float(cantidad)
    except:
        logging.error ('La cantidad no es correcta')
        return None
    if digits_integer < 1:
        return canidad

    template = 1
    fin = False

    tens_lim = 10**digits_integer
    
    while not fin:
        if (cantidad / template) < tens_lim:
            fin = True
            break
        template = template * 1000

    if template >= 1000000000:
        cantidad_out = cantidad/1000000000
        symbol = 'B'
    elif template >= 1000000:
        cantidad_out = cantidad/1000000
        symbol = 'M'
    elif template >= 1000:
        cantidad_out = cantidad/1000
        symbol = 'K'
    else:
        cantidad_out = cantidad
        symbol = ''
    
    if cantidad_out < 10: 
        currency = "{:,.2f}".format(cantidad_out)
    else:
        currency = "{:,.1f}".format(cantidad_out)
    currency += symbol

    return currency


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
                       font_size=10,
                       title_font_size=13,
                       xaxis_rangeslider_visible=False, 
                       yaxis={'side': 'left'} ,
                       yaxis2={'side': 'right'} ,
                       title_text='Historico', 
                       title_x = 0.5,
                       title_xanchor = 'center',
                       margin=dict(l=0, r=0, t=40, b=40),
                       hovermode="x unified"
    )

    return fig1

def layout_getFigura_split (symbolSpread, base = False):
    fig3 = None

    spread_list = globales.G_RTlocalData_.appObj_.contractCode2list(symbolSpread)
    if len(spread_list) < 1:
        return fig3

    if len(spread_list) > 1:  
        spread_list.append ({'action':'BAG', 'ratio': 1, 'code': symbolSpread})

    fig3 = go.Figure()
    fig3 = make_subplots(specs=[[{"secondary_y": True}]])

    for comp in spread_list:
        symbol = comp['code']
        contrato = globales.G_RTlocalData_.contractGetBySymbol(symbol)
        if not contrato:
            logging.error ("Error cargando grafico historico de %s. No tenemos el contrato cargado en RT_Data", symbol)
            break
        if contrato['dbPandas']:
            df_comp = contrato['dbPandas'].dbGetDataframeComp()
            if base:
                base_level = df_comp.iloc[0]["close"]
            else:
                base_level = 0
            if comp ['action'] == 'BAG':
                eje_sec = True
                linel = dict(color='rgb(150,150,150)', width=1, dash='dash')
            else:
                eje_sec = False
                linel = dict(width=2)
            fig3.add_trace(
                go.Scatter(
                    x=df_comp.index, 
                    y=(df_comp["close"]-base_level), 
                    line=linel,
                    mode="lines", 
                    connectgaps = True, 
                    name = symbol
                ),
                secondary_y=eje_sec
            )

    
    fig3.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
            dict(bounds=[21.1, 15], pattern="hour"),  # hide hours outside of 9.30am-4pm
            #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
        ]
    )

    fig3.update_layout(showlegend=True, 
                       font_size=10,
                       title_font_size=13,
                       xaxis_rangeslider_visible=False, 
                       title_text='Componentes', 
                       title_x = 0.5,
                       title_xanchor = 'center',
                       margin=dict(l=0, r=0, t=40, b=40),
                       legend_x=0, legend_y=1,
                       hovermode="x unified"
                    )

    return fig3

















