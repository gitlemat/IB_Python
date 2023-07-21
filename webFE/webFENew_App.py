from dash import Dash
import webFE.webFENew_Layout
import dash_bootstrap_components as dbc
import logging

logging.getLogger('werkzeug').setLevel(logging.ERROR)

external_stylesheets = [dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP]
appDashFE_ = Dash(
    external_stylesheets=external_stylesheets,
)
appDashFE_.title = "IB RODSIC"

appDashFE_.layout = webFE.webFENew_Layout.layout_init