#!/usr/bin/env python
"""Implements a helpdesk-api"""

import ConfigParser
import subprocess
import re
import collections
import os
import time
import datetime
import thread
import requests

from flask import Flask, url_for
from flask import request
from flask import json
from flask import Response
from flask import jsonify
from flask import g

from subprocess import call
from functools import wraps
#from helpdesk_api_model import *
from sqlalchemy import or_, and_
from sqlalchemy.sql import text
from flask.ext.sqlalchemy import get_debug_queries
from sqlalchemy import create_engine
from flask.ext.sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api,  reqparse, fields, marshal
from flask.ext.httpauth import HTTPBasicAuth
#engine = create_engine('mysql://helpdesk:h2lpd2sk@127.0.0.1:6000/HelpDeskDev', pool_recycle=280, echo=True)


app = Flask(__name__)
db = SQLAlchemy()
api = Api(app)
auth = HTTPBasicAuth()

#Leo la Configuracion General
config = ConfigParser.ConfigParser()
config.read('api.conf')

"""app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://' + config.get('General', 'dbuser') + ":" \
                          + config.get('General', 'dbpass') + '@' + config.get('General', 'dbhost')\
                          + '/' + config.get('General', 'dbname')"""

#engine = create_engine('mysql://helpdesk:h2lpd2sk@127.0.0.1:6000/HelpDeskDev')#, pool_recycle=280, echo=True)
#conn = engine.connect()

#Autenticacion
"""def check_auth(username, password):
    if username == "admin" and password == "nolase":
        return 1
    else:
        return 0
"""
def authenticate():
    message = {'message': "Authenticate."}
    resp = jsonify(message)

    resp.status_code = 401
    resp.headers['WWW-Authenticate'] = 'Basic realm="TrabajoFinal-API"'

    return resp

@auth.get_password
def get_password(username):
    if username == 'admin':
        return '123qwe'
    return None


#Comienzo API
@app.route('/')
def api_root():
    message = {'status': 200, 'message': 'api'}
    resp = jsonify(message)
    resp.status_code = 200
    return resp



task_fields = {
    'USER': fields.String,
    'PID': fields.String,
    'CPU': fields.String,
    'MEM': fields.String,
    'VSZ': fields.String,
    'RSS': fields.String,
    'TTY': fields.String,
    'STAT': fields.String,
    'START': fields.String,
    'TIME': fields.String,
    'COMMAND': fields.String
}

message_fields = {
    'Message' : fields.String
}

class ListAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, location='json')
        self.reqparse.add_argument('description', type=str, location='json')
        self.reqparse.add_argument('done', type=bool, location='json')
        super(ListAPI, self).__init__()

    def get(self):
        procesos = []
        p = subprocess.Popen(['ps', '-faxu', '--columns', '1000'], stdout=subprocess.PIPE)
        (output, err) = p.communicate()
        lines = output.splitlines()
        for line in lines[1:]:
            values = line.split()
            procesos.append({'USER': values[0],
            'PID': values[1],
            'CPU': values[2],
            'MEM': values[3],
            'VSZ': values[4],
            'RSS': values[5],
            'TTY': values[6],
            'STAT': values[7],
            'START': values[8],
            'TIME': values[9],
            'COMMAND': ' '.join(values[10:])})
        return {'procesos': [marshal(task, task_fields) for task in procesos]}

class API(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, location='json')
        self.reqparse.add_argument('description', type=str, location='json')
        self.reqparse.add_argument('done', type=bool, location='json')
        super(API, self).__init__()

    def post(self, command):
        p = subprocess.Popen([str(command)], stdout=subprocess.PIPE)
        (output, err) = p.communicate()
        if output == "":
            message = {'Message': 'Proceso '+ str(command) + ' lanzado exitosamente'}
        else:
            message = {'Message': output}
        return {'Respuesta': marshal(message, message_fields)}
    
    def put(self, pri, id):
        p = subprocess.Popen(['renice', pri, str(id)], stdout=subprocess.PIPE)
        (output, err) = p.communicate()
        message = {'Message' : output}
        return {'Respuesta': marshal(message, message_fields)}

    def delete(self, id):
        p = subprocess.Popen(['kill', '-9', str(id)], stdout=subprocess.PIPE)
        (output, err) = p.communicate()
        if output == "":
            message = {'Message': 'Proceso '+ str(id) + ' ha sido borrado'}
        else:
            message = {'Message': output}
        return {'Respuesta': marshal(message, message_fields)}

api.add_resource(ListAPI, '/api/procesos', endpoint='procesos')
api.add_resource(API, '/api/eliminar/<int:id>', endpoint='eliminar')
api.add_resource(API, '/api/<int:id>/prioridad/<string:pri>',endpoint='prioridad')
api.add_resource(API, '/api/nuevo/<string:command>', endpoint='nuevo')


db.init_app(app)
if __name__ == '__main__':
    app.config.update(DEBUG=config.get('General', 'debug'))
    app.run(host=config.get('General', 'host'),\
            port=int(config.get('General', 'port')))

