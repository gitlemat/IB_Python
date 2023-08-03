from flask import Flask, request, jsonify
from dash import Dash
import webFE.webFENew_Layout
import dash_bootstrap_components as dbc
import logging

logging.getLogger('werkzeug').setLevel(logging.ERROR)

server = Flask(__name__)

external_stylesheets = [dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP]
appDashFE_ = Dash(
    server=server,
    external_stylesheets=external_stylesheets,
)
appDashFE_.title = "IB RODSIC"

appDashFE_.layout = webFE.webFENew_Layout.layout_init

###################################
# Ahora la REST

events_list = [
   {
       "id":0,
       "event_type": "pull_request",
       "event_name": "change_event"
   },


   {
       "id":1,
       "event_type":"release",
       "event_name":"deployment_event"
   },
   {
       "id":2,
       "event_type":"push",
       "event_name":"workflow_event"
   },
   {
       "id":3,
       "event_type": "pull_request_merged",
       "event_name":"deployment_event"
   }
]

@server.route('/restAPI', methods=['GET'])
def restAPI():

   if request.method == 'GET':
       if len(events_list) > 0:
           # encode list of events in json
           return jsonify(events_list)
       else:
           'Event not found', 404