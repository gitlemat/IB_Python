import webFE.webFENew_Ordenes
import webFE.webFENew_Contratos
import webFE.webFENew_Strategies
import webFE.webFENew_Account
import webFE.webFENew_Logs
import webFE.webFENew_Math
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

# Los estilos están en el folder assets
def layout_sidebar():

    sidebar_header = dbc.Row(
        [
            dbc.Col(html.Div("RODSIC", className="display-5")),
            dbc.Col(
                html.Button(
                    # use the Bootstrap navbar-toggler classes to style the toggle
                    html.Span(className="navbar-toggler-icon"),
                    className="navbar-toggler",
                    # the navbar-toggler classes don't set color, so we do it here
                    style={
                        "color": "rgba(0,0,0,.5)",
                        "border-color": "rgba(0,0,0,.1)",
                    },
                    id="toggle-sidebar",
                ),
                # the column containing the toggle will be only as wide as the
                # toggle, resulting in the toggle being right aligned
                width="auto",
                # vertically align the toggle in the center
                align="center",
            ),
        ]
    )

    sidebar = html.Div(
        [
            sidebar_header,
            # we wrap the horizontal rule and short blurb in a div that can be
            # hidden on a small screen
            html.Div(
                [
                    html.Hr(),
                    html.P(
                        "Yate con enanos",
                        className="lead",
                    ),
                ],
                id="blurb",
            ),
            # use the Collapse component to animate hiding / revealing links
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavLink("Summary", id="nav-1", href="/Summary", active="exact"),
                        dbc.NavLink("Estrategias", id="nav-2", href="/Estrategias", active="exact"),
                        dbc.NavLink("Contratos", id="nav-3", href="/Contratos", active="exact"),
                        dbc.NavLink("Ordenes", id="nav-4", href="/Ordenes", active="exact"),
                        dbc.NavLink("Math", id="nav-5", href="/Math", active="exact"),
                        dbc.NavLink("Cuenta", id="nav-6", href="/Account", active="exact"),
                        dbc.NavLink("Logs", id="nav-7   ", href="/Logs", active="exact"),
                    ],
                    vertical=True,
                    pills=True,
                ),
                id="collapse-sidebar",
            ),
        ],
        id="sidebar",
    )    

    content = html.Div(id="page-content-main")

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

@callback(Output("page-content-main", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        return webFE.webFENew_Summary.layout_summary_tab()
    if pathname == "/Summary":
        return webFE.webFENew_Summary.layout_summary_tab()
    elif pathname == "/Estrategias":
        return webFE.webFENew_Strategies.layout_strategies_tab()
    elif pathname == "/Contratos":
        return webFE.webFENew_Contratos.layout_contratos_tab()
    elif pathname == "/Ordenes":
        return webFE.webFENew_Ordenes.layout_ordenes_tab()
    elif pathname == "/Math":
        return webFE.webFENew_Math.layout_math_tab()
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

# Callback para el menu lateral/superior
@callback(
    Output("collapse-sidebar", "is_open"),
    [Input("toggle-sidebar", "n_clicks")],
    [State("collapse-sidebar", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

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