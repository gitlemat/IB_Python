import webFE.webFENew_Ordenes
import webFE.webFENew_Contratos
import webFE.webFENew_Strategies
import webFE.webFENew_Logs
import webFE.webFENew_Summary
from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc

import globales

def layout_init():

    layout = dbc.Container(
        [
            layout_sidebar(),
            modal_error(),
        ], fluid=True
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
                    dbc.Tab(label="Summary", tab_id="tab-summary"),
                    dbc.Tab(label="Estrategias", tab_id="tab-estrat"),
                    dbc.Tab(label="Contratos", tab_id="tab-contrat"),
                    dbc.Tab(label="Ordenes", tab_id="tab-ordenes"),
                    dbc.Tab(label="Logs", tab_id="tab-logs"),
                ],
                id="tabs",
                active_tab="tab-estrat",
            ),
            html.Div(id="tabContent"),
        ]
    )

    return tabs

# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

def layout_sidebar():

    sidebar = html.Div(
        [
            html.H2("RODSIC", className="display-4"),
            html.Hr(),
            html.P(
                "Yate con enanos", className="lead"
            ),
            dbc.Nav(
                [
                    dbc.NavLink("Summary", href="/Summary", active="exact"),
                    dbc.NavLink("Estrategias", href="/Estrategias", active="exact"),
                    dbc.NavLink("Contratos", href="/Contratos", active="exact"),
                    dbc.NavLink("Ordenes", href="/Ordenes", active="exact"),
                    dbc.NavLink("Logs", href="/Logs", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        style=SIDEBAR_STYLE,
    )

    content = html.Div(id="page-content", style=CONTENT_STYLE)

    layout = html.Div([dcc.Location(id="url"), sidebar, content])

    return layout

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

@callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/Summary":
        return webFE.webFENew_Summary.layout_summary_tab()
    elif pathname == "/Estrategias":
        return webFE.webFENew_Strategies.layout_strategies_tab()
    elif pathname == "/Contratos":
        return webFE.webFENew_Contratos.layout_contratos_tab()
    elif pathname == "/Ordenes":
        return webFE.webFENew_Ordenes.layout_ordenes_tab()
    elif pathname == "/Logs":
        return webFE.webFENew_Logs.layout_logs_tab()
    # If the user tries to reach a different page, return a 404 message
    return html.Div(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ],
        className="p-3 bg-light rounded-3",
    )

# Callback para cambiar tab
@callback(Output("tabContent", "children"), [Input("tabs", "active_tab")])
def switch_tab(at):
    if at == "tab-contrat":
        return webFE.webFENew_Contratos.layout_contratos_tab()
    elif at == "tab-estrat":
        return webFE.webFENew_Strategies.layout_strategies_tab()
    elif at == "tab-ordenes":
        return webFE.webFENew_Ordenes.layout_ordenes_tab()
    elif at == "tab-logs":
        return webFE.webFENew_Logs.layout_logs_tab()
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