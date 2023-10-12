from dash import MATCH, ALL, Input, Output, State, ctx, no_update, callback
from dash import html
from dash import dcc
from dash.exceptions import PreventUpdate

import dash_bootstrap_components as dbc
import logging
import globales
import random

logger = logging.getLogger(__name__)
logger_root = logging.getLogger()

def layout_logs_tab ():
    log_handler = logger_root.handlers
    #logging.info ('Handlers: %s', log_handler)
    filename = log_handler[0].baseFilename
    with open(filename) as f:
        lines = f.readlines()

    logtext = []
    for line in lines[1:]:
        textL = html.Pre(
            children=line, 
            className='mb-0',
            style={
                'font-size': '12px'
            })
        logtext.append(textL)
    
    tablogs = [
            dbc.Row(
                [
                    html.P("Logs de Hoy", className='text-left text-secondary mb-4 ps-0 display-6'),
                    html.Hr()
                ]
            ),
            dbc.Row
            (
                [
                    'Tamaño cola Prio    : ' + str(globales.G_RTlocalData_.appObj_.CallbacksQueuePrio_.qsize()) + '\n',
                    'Tamaño cola Non-Prio: ' + str(globales.G_RTlocalData_.appObj_.CallbacksQueue_.qsize()) + '\n'
                ]
            ),
            dbc.Row
            (
                logtext
            )
    ]
    logging.info('Prepared')

    return tablogs