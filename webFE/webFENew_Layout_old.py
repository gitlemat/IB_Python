import webFE.webFENew_Ordenes
import webFE.webFENew_ContratosIB
import webFE.webFENew_Strategies
import webFE.webFENew_Account
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
            modal_error('reloadStrategiesOK'),
        ], fluid=True
    )

    return layout

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
                    dbc.NavLink("Cuenta", href="/Account", active="exact"),
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

def modal_error(usecase):
    modal = html.Div(
        [
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Deafult", id = "modal_" + usecase)),
                    dbc.ModalBody("Default", id = "modal_" + usecase + "_Body"),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close", id="modal_" + usecase + "_boton_close", className="ms-auto", n_clicks=0
                        )
                    ),
                ],
                id="modal_" + usecase + "_main",
                is_open=False,
            ),
        ]
    )
    return modal

@callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        return webFE.webFENew_Summary.layout_summary_tab()
    if pathname == "/Summary":
        return webFE.webFENew_Summary.layout_summary_tab()
    elif pathname == "/Estrategias":
        return webFE.webFENew_Strategies.layout_strategies_tab()
    elif pathname == "/Contratos":
        return webFE.webFENew_ContratosIB.layout_contratos_tab()
    elif pathname == "/Ordenes":
        return webFE.webFENew_Ordenes.layout_ordenes_tab()
    elif pathname == "/Account":
        return webFE.webFENew_Account.layout_account_tab()
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