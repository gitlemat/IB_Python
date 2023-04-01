import webFE.webFENew_Ordenes
import webFE.webFENew_Contratos
import webFE.webFENew_Strategies
from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc

import globales

def layout_init():

    layout = dbc.Container(
        [
            layout_tabs(),
            modal_error(),
            modal_contratoOrdenCreate(),
        ]
    )

    return layout

def layout_tabs():

    chilText = "Prueba Front-End-2 IB"

    allReady = True
    #return layout
    if globales.G_RTlocalData_ == None:
        allReady = False
        chilText += " G_RTlocalData_ No está listo"
    elif globales.G_RTlocalData_.appObj_ == None:
        allReady = False
        chilText += " G_RTlocalData_.appObj_ No está listo"
    elif globales.G_RTlocalData_.appObj_.initReady_ == False:
        chilText += " G_RTlocalData_.appObj_.initReady No está listo"
        allReady = False
        
    if not allReady:
        chil1 = [
            html.H1(
                children=chilText,
                style={"textAlign": "center"}
            ),
        ]
        
        layout = html.Div(
            id="parent",
            children=chil1
        )
        return layout
    
    tabs = html.Div(
        [
            dbc.Tabs(
                [
                    dbc.Tab(label="Estrategias", tab_id="tab-estrat"),
                    dbc.Tab(label="Contratos", tab_id="tab-contrat"),
                    dbc.Tab(label="Ordenes", tab_id="tab-ordenes"),
                ],
                id="tabs",
                active_tab="tab-estrat",
            ),
            html.Div(id="tabContent"),
        ]
    )

    return tabs

def modal_error():
    modal = html.Div(
        [
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Deafult", id = "modalErrorHeader")),
                    dbc.ModalBody("Default", id = "modalErrorBody"),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close", id="modal_boton_close", className="ms-auto", n_clicks=0
                        )
                    ),
                ],
                id="modal_error_main",
                is_open=False,
            ),
        ]
    )
    return modal

def modal_contratoOrdenCreate():

    orderSymbol = dcc.Input(
        id = "contract_orders_create_symbol",
        type = "text",
        readOnly = True,
        placeholder = "",
    )

    orderQty = dcc.Input(
        id = "contract_orders_create_qty",
        type = "number",
        placeholder = "0",
    )

    orderLmtPrice = dcc.Input(
        id = "contract_orders_create_LmtPrice",
        type = "number",
        placeholder = "0",
    )

    orderAction = dcc.Dropdown(
        options = ['BUY', 'SELL'], 
        value = 'BUY', 
        id = 'contract_orders_create_action'
    )

    orderType = dcc.Dropdown(
        options = ['MKT', 'LMT', 'STP', 'MKTGTC', 'LMTGTC', 'STPGTC'], 
        value = 'MKT', 
        id='contract_orders_create_orderType'
    )

    responseBody = html.Div([
        html.P('Contract Symbol: ',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderSymbol,
        html.P('Order Action:',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderAction,
        html.P('Order Type:',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderType,
        html.P('Order Qty:',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderQty,
        html.P('Order LMT Price:',
            style={'margin-top': '8px', 'margin-bottom': '4px'},
            className='font-weight-bold'),
        orderLmtPrice,
    ])
    
    modal = html.Div(
        [
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Crear Ordem", id = "modalContratoOrdenCreateHeader")),
                    dbc.ModalBody(responseBody, id = "modalContratoOrdenCreateBody"),
                    dbc.ModalFooter([
                        dbc.Button(
                            "Crear", id="modalContratoOrdenCreate_boton_create", className="ms-auto", n_clicks=0
                        ),
                        dbc.Button(
                            "Close", id="modalContratoOrdenCreate_boton_close", className="ms-auto", n_clicks=0
                        )
                    ]),
                ],
                id="modalContratoOrdenCreate_main",
                is_open=False,
            ),
        ]
    )
    return modal

# Callback para cambiar tab
@callback(Output("tabContent", "children"), [Input("tabs", "active_tab")])
def switch_tab(at):
    if at == "tab-contrat":
        return webFE.webFENew_Contratos.layout_contratos_tab()
    elif at == "tab-estrat":
        return webFE.webFENew_Strategies.layout_strategies_tab()
    elif at == "tab-ordenes":
        return webFE.webFENew_Ordenes.layout_ordenes_tab()
    return html.P("This shouldn't ever be displayed...")

# Callback para colapsar o mostrar filas Generico
@callback(
    Output({'role': 'colapse', 'index': MATCH}, "is_open"),
    Input({'role': 'boton', 'index': MATCH}, "n_clicks"),
    State({'role': 'colapse', 'index': MATCH}, "is_open"),
    prevent_initial_call = True,
)
def toggle_colapse_generic(n_button, is_open):
    if n_button:
        return not is_open
    return is_open