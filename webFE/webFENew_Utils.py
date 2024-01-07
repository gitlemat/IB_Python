import logging
import globales
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
import random
from dash import html

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


def layout_getFigureToday (contrato):
    
    dfToday = contrato['dbPandas'].dbGetDataframeToday()
    LastPrice = None
    if len(dfToday.index) > 0:
        LastPrice = dfToday['close'].iloc[-1]
    fig2 = go.Figure()

    # Valores de LAST
    #fig2.add_trace(go.Scatter(x=dfToday.index, y=dfToday["BID"], mode="lines", line_color="blue", connectgaps = True))
    #fig2.add_trace(go.Scatter(x=dfToday.index, y=dfToday["ASK"], mode="lines", line_color="green", connectgaps = True))
    #fig2.add_trace(go.Scatter(x=dfToday.index, y=dfToday["LAST"], mode="lines", line_color="crimson", connectgaps = True))
    fig2.add_trace(
        go.Candlestick(
            x=dfToday.index, 
            open=dfToday['open'], 
            high=dfToday['high'],
            low=dfToday['low'],
            close=dfToday['close'],
            hoverlabel_split=True
        )
    )
    if len(dfToday.index) > 0 and LastPrice != None:
        fig2.add_annotation(
            x = dfToday.index[-1],
            y = LastPrice,
            text = f"{LastPrice:0.2f}",
            xshift=20,
            yshift=0,
            bordercolor='green',
            borderwidth=2,
            bgcolor="#CFECEC",
            opacity=0.8,
            showarrow=False
        )
    
    #######
    # Esto es por si quiero controlar el rango de Y y concentrarme en el candle
    # Seria util cuando estamos lejos de los niveñes de las zonas
    #
    '''
    levelRanges = getZonesRanges(estrategia)
    if len (dfToday) > 0:
        minLevelToday = min (dfToday['open'], dfToday['high'], dfToday['low'], dfToday['close'])
        maxLevelToday = max (dfToday['open'], dfToday['high'], dfToday['low'], dfToday['close'])
    else:
        minLevelToday = levelRanges['minLevel']
        maxLevelToday = levelRanges['maxLevel']

    rangeLevelToday = maxLevelToday - minLevelToday
    display_min = minLevelToday
    display_max = maxLevelToday
    
    if levelRanges['minLevel'] < minLevelToday:
        display_min = minLevelToday - rangeLevelToday*0.25
    if levelRanges['maxLevel'] > maxLevelToday:
        display_max = maxLevelToday + rangeLevelToday*0.25
    
    '''
    #######

    fig2.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
            dict(bounds=[20.25, 15.16], pattern="hour"),  # hide hours outside of 9.30am-4pm
            #dict(values=["2020-12-25", "2021-01-01"]),  # hide holidays (Christmas and New Year's, etc)
        ]
    )
    fig2.update_yaxes(
        tickformat='.2f'
    )

    rannn = str(random.randint(0,1000))
    logging.debug ('Grafico actualizado con %s', rannn)
    fig2.update_layout(showlegend=False, 
                       font_size=10,
                       title_font_size=13,
                       xaxis_rangeslider_visible=False, 
                       yaxis={'side': 'right'} ,
                       title_text='Datos Tiempo Real Hoy', 
                       title_x = 0.5,
                       title_xanchor = 'center',
                       margin=dict(l=0, r=0, t=40, b=40),
                       hovermode="x unified")

    contrato['dbPandas'].toPrint = False

    return fig2

def getZonesRanges (estrategia):
    maxLevel = None
    minLevel = None
    for zone in estrategia['classObject'].zones_:  
        if maxLevel == None:
            maxLevel = zone['orderBlock'].Price_
        if minLevel == None:
            minLevel = zone['orderBlock'].Price_
        
        maxLevel = max (maxLevel, zone['orderBlock'].PrecioSL_, zone['orderBlock'].PrecioTP_)
        minLevel = max (minLevel, zone['orderBlock'].PrecioSL_, zone['orderBlock'].PrecioTP_)

    ret = {'maxLevel': maxLevel, 'minLevel': minLevel}

    return ret


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
                marker_color='rgb(255, 190, 190)',
                name='Volumen'
            ),
            secondary_y=False
        )
        
        fig1.add_trace(
            go.Candlestick(
                x=df_comp.index, 
                open=df_comp['open'], 
                high=df_comp['high'],
                low=df_comp['low'],
                close=df_comp['close'],
                hoverlabel_split=True
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
                       hovermode="x unified",
                       dragmode=False
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

def layout_getStrategyPenRuTableOrders (estrategia, update = False):

    if estrategia == None:
        return None
    #orden = globales.G_RTlocalData_.orderGetByOrderId(lOrderId)
    if estrategia['classObject'] == None:
        return None
    if estrategia['classObject'].ordersUpdated_ == False and update == True:
        logging.debug ('Tabla de ordenes en Strategia no actualizado. No hay datos nuevos')
        return None

    symbol = estrategia['classObject'].symbol_

    insideDetailsTableHeader = [
        html.Thead(
            html.Tr(
                [
                   html.Th(""), 
                   html.Th("Order Id"),
                   html.Th("Perm Id", className = 'd-none d-md-table-cell'),
                   html.Th("Lmt"),
                   html.Th("Type", className = 'd-none d-md-table-cell'),
                   html.Th("Action", className = 'd-none d-md-table-cell'),
                   html.Th("Status"),
                   html.Th("Qty"),
                   html.Th("Fix"),
                ], style={'color':'#ffffff','background-color':'#636363'}
            )   
        )
    ]

    insideDetailsTableBodyInside = []

    for orderBlock in estrategia['classObject'].orderBlocks_:
        #ordenParent = globales.G_RTlocalData_.orderGetByOrderId (zone['OrderId'])
        ordenParent = globales.G_RTlocalData_.orderGetByOrderId (orderBlock.orderId_)
        fixOCA = False
        fixParent = False
        if orderBlock.toFix == 1:
            fixParent = True
            # Parent Rota y fix necesario
        if orderBlock.toFix == 2:
            fixOCA = True
            # OCA Rota y fix necesario
        if orderBlock.toFix == 3:
            fixParent = True
            fixOCA = True
        if ordenParent:
            posParent = ordenParent['order'].totalQuantity
            typeParent = ordenParent['order'].orderType
            if ordenParent['params'] != None and 'status' in ordenParent['params']:
                statusParent = ordenParent['params']['status']
            elif orderBlock.BracketOrderFilledState_ in ['ParentFilled', 'ParentFilled+F', 'ParentFilled+EP', 'ParentFilled+EC']:
                statusParent = 'Filled'
            else:
                statusParent = 'N/A'
                #statusParent = 'PreSubmitted'
            lmtParent = ordenParent['order'].lmtPrice
            actionParent = ordenParent['order'].action
            if ordenParent['order'].orderType == 'STP':  # No va a pasar nunca
                lmtParent = ordenParent['order'].auxPrice
        else:
            posParent = orderBlock.Qty_
            lmtParent = orderBlock.Price_
            if orderBlock.B_S_ == 'S':
                actionParent = 'SELL'
            else:
                actionParent = 'BUY'
            typeParent = 'LMT'
            if orderBlock.BracketOrderFilledState_ in ['ParentFilled', 'ParentFilled+F', 'ParentFilled+EP', 'ParentFilled+EC']:
                statusParent = 'Filled'
            else:
                statusParent = 'N/A'
            #statusParent = 'PreSubmitted'

        if actionParent == 'SELL':
            posParent = posParent * (-1)
        lmtParent = formatCurrency(lmtParent)

        #ordenTP = globales.G_RTlocalData_.orderGetByOrderId (zone['OrderIdTP'])
        ordenTP = globales.G_RTlocalData_.orderGetByOrderId (orderBlock.orderIdTP_)
        if ordenTP:
            posTP = ordenTP['order'].totalQuantity
            typeTP = ordenTP['order'].orderType
            if ordenTP['params'] != None and 'status' in ordenTP['params']:
                statusTP = ordenTP['params']['status']
            else:
                statusTP = 'N/A'
            lmtTP = ordenTP['order'].lmtPrice
            actionTP = ordenTP['order'].action
            if ordenTP['order'].orderType == 'STP':
                lmtTP = ordenTP['order'].auxPrice
        else:
            posTP = orderBlock.Qty_
            lmtTP = orderBlock.PrecioTP_
            actionTP = "SELL" if actionParent == "BUY" else "BUY"
            typeTP = 'LMT'
            statusTP = 'N/A'

        if actionTP == 'SELL':
            posTP = posTP * (-1)
        lmtTP = formatCurrency(lmtTP)

        #ordenSL = globales.G_RTlocalData_.orderGetByOrderId (zone['OrderIdSL'])
        ordenSL = globales.G_RTlocalData_.orderGetByOrderId (orderBlock.orderIdSL_)
        if ordenSL:
            posSL = ordenSL['order'].totalQuantity
            typeSL = ordenSL['order'].orderType
            if ordenSL['params'] != None and 'status' in ordenSL['params']:
                statusSL = ordenSL['params']['status']
            else:
                statusSL = 'N/A'
            lmtSL = ordenSL['order'].lmtPrice
            actionSL = ordenSL['order'].action
            if ordenSL['order'].orderType == 'STP':
                lmtSL = ordenSL['order'].auxPrice
            if ordenSL['order'].action == 'SELL':
                posSL = posSL * (-1)
        else:
            posSL = orderBlock.Qty_
            lmtSL = orderBlock.PrecioSL_
            actionSL = "SELL" if actionParent == "BUY" else "BUY"
            typeSL = 'STP'
            statusSL = 'N/A'

        if actionSL == 'SELL':
            posSL = posSL * (-1)
        lmtSL = formatCurrency(lmtSL)

        backgroundColorParent = '#c1c2c9'
        backgroundColorTP = '#e4e5ed'
        backgroundColorSL = '#e4e5ed'
        if statusParent in ['Filled']:
            backgroundColorParent = '#caf5c9' # Todo bien
        if statusParent in ['N/A']:
            if orderBlock.BracketOrderFilledState_ in ['ParentFilled', 'ParentFilled+F']:
                backgroundColorParent = '#caf5c9' # Bien
            else:
                backgroundColorParent = '#d6bfba' # Mal

        if statusTP in ['Filled']:
            backgroundColorTP = '#caf5c9'
        if statusTP in ['N/A']:
            backgroundColorTP = '#cf5338'
        if statusSL in ['Filled']:
            backgroundColorSL = '#cf5338'
        if statusSL in ['N/A']:
            backgroundColorSL = '#cf5338'

        if fixParent:
            boton_color_parent = '#000000'
            disableParentFix = False
        else:
            boton_color_parent = '#A5A5A5'
            disableParentFix = True

        if fixOCA:
            boton_color_oca = '#000000'
            disableOcaFix = False
        else:
            boton_color_oca = '#A5A5A5'
            disableOcaFix = True

        #id="{"orderIntId":"HEM4-2HEN4+HEQ4PentagramaRu-3.0-2.8-4.5","role":"boton_fix","symbol":"HEM4-2HEN4+HEQ4"}

        if orderBlock.orderId_ == None:
            id_boton = {'role': 'boton_fix', 'orderIntId': str(orderBlock.intId_), 'symbol': symbol}
        else:
            id_boton = {'role': 'boton_fix', 'orderId': str(orderBlock.orderId_), 'symbol': symbol}

        insideDetailsStratParent = html.Tr(
            [
                html.Td("Parent", style={'background-color':'transparent'}), 
                #html.Td(str(zone['OrderId'])),
                #html.Td(str(zone['OrderPermId'])),
                html.Td(str(orderBlock.orderId_), style={'background-color':'transparent'}),
                html.Td(str(orderBlock.orderPermId_), className = 'd-none d-md-table-cell', style={'background-color':'transparent'}),
                html.Td(str(lmtParent), style={'background-color':'transparent'}),
                html.Td(str(typeParent), className = 'd-none d-md-table-cell', style={'background-color':'transparent'}),
                html.Td(str(actionParent), className = 'd-none d-md-table-cell', style={'background-color':'transparent'}),
                html.Td(str(statusParent), style={'background-color':'transparent'}),
                html.Td(str(posParent), style={'background-color':'transparent'}),
                html.Td(dbc.Button(html.I(className="bi bi-bandaid me-2"),id=id_boton, style={'color': boton_color_parent, 'background-color': 'transparent', 'border-color': 'transparent'}, disabled=disableParentFix), style={'background-color':'transparent'}),
            ], style={'color':'#000000','background-color':backgroundColorParent}
        )

        insideDetailsStratTP = html.Tr(
            [
                html.Td("TP", style={"textAlign": "right", 'background-color':'transparent'}), 
                #html.Td(str(zone['OrderIdTP'])),
                #html.Td(str(zone['OrderPermIdTP'])),
                html.Td(str(orderBlock.orderIdTP_), style={'background-color':'transparent'}),
                html.Td(str(orderBlock.orderPermIdTP_), className = 'd-none d-md-table-cell', style={'background-color':'transparent'}),
                html.Td(str(lmtTP), style={'background-color':'transparent'}),
                html.Td(str(typeTP), className = 'd-none d-md-table-cell', style={'background-color':'transparent'}),
                html.Td(str(actionTP), className = 'd-none d-md-table-cell', style={'background-color':'transparent'}),
                html.Td(str(statusTP), style={'background-color':'transparent'}),
                html.Td(str(posTP), style={'background-color':'transparent'}),
                html.Td(dbc.Button(html.I(className="bi bi-bandaid me-2"),id={'role': 'boton_fix', 'orderId': str(orderBlock.orderIdTP_), 'symbol': symbol}, style={'color': boton_color_oca, 'background-color': 'transparent', 'border-color': 'transparent'}, disabled=disableOcaFix), style={'background-color':'transparent'}),
            ], style={'color':'#000000','background-color':backgroundColorTP}
        )

        insideDetailsStratSL = html.Tr(
            [
                html.Td("SL", style={"textAlign": "right", 'background-color':'transparent'}), 
                #html.Td(str(zone['OrderIdSL'])),
                #html.Td(str(zone['OrderPermIdSL'])),
                html.Td(str(orderBlock.orderIdSL_), style={'background-color':'transparent'}),
                html.Td(str(orderBlock.orderPermIdSL_), className = 'd-none d-md-table-cell', style={'background-color':'transparent'}),
                html.Td(str(lmtSL), style={'background-color':'transparent'}),
                html.Td(str(typeSL), className = 'd-none d-md-table-cell', style={'background-color':'transparent'}),
                html.Td(str(actionSL), className = 'd-none d-md-table-cell', style={'background-color':'transparent'}),
                html.Td(str(statusSL), style={'background-color':'transparent'}),
                html.Td(str(posSL), style={'background-color':'transparent'}),
                html.Td(dbc.Button(html.I(className="bi bi-bandaid me-2"),id={'role': 'boton_fix', 'orderId': str(orderBlock.orderIdSL_), 'symbol': symbol}, style={'color': boton_color_oca, 'background-color': 'transparent', 'border-color': 'transparent'}, disabled=disableOcaFix), style={'background-color':'transparent'}),
            ], style={'color':'#000000','background-color':backgroundColorSL}
        )

        insideDetailsStratEmpty = html.Tr("", style={'height':'10px'})

        insideDetailsTableBodyInside.append(insideDetailsStratParent)
        insideDetailsTableBodyInside.append(insideDetailsStratTP)
        insideDetailsTableBodyInside.append(insideDetailsStratSL)
        insideDetailsTableBodyInside.append(insideDetailsStratEmpty)


    insideDetailsTableBody = [html.Tbody(insideDetailsTableBodyInside)]
    estrategia['classObject'].ordersUpdated_ = False

    ret = dbc.Table(
        insideDetailsTableHeader + insideDetailsTableBody, 
        bordered=True
    )

    return ret
















