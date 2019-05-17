#!/usr/bin/env python3

from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import json, ast
from utils import create_style_policy, init_dpapi, exceptions, update_policy, append_handlers

app = Flask(__name__)
CORS(app)


@app.errorhandler(exceptions.ApiError)
def handler_error(error):
    message = {
            'status': error.status_code,
            'message': error.message
    }
    resp = jsonify(message)
    resp.status_code = error.status_code
    return resp


def success_response(msg):
    message = {
        'status': 200,
        'message': msg
    }
    resp = jsonify(message)
    resp.status_code = 200
    return resp


@app.route("/", methods=['GET', 'POST'])
def hello():
    return "Hi"


@app.route("/api/mq_handler/create", methods=['post'])
def create_mq_handler():
    try:
        json_data, handlers = ast.literal_eval(request.data.decode()), []
        api = init_dpapi(request.args)
        if isinstance(json_data, list):
            for handler_obj in json_data:
                handler = api.mq_handler.create(handler_obj["name"], handler_obj["queue_manager"], handler_obj["get_queue"], handler_obj["state"]) 
                handlers.append(handler["name"])
        else:       
            handler = api.mq_handler.create(json_data["name"], json_data["queue_manager"], json_data["get_queue"], json_data["state"])
            return success_response('MQ Handler "' + handler["name"] + '" was created')
        return success_response('MQ Handlers ' + str(handlers).strip('[]') + ' were created')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@app.route("/api/http_handler/create", methods=['post'])
def create_http_handler():
    try:
        json_data = ast.literal_eval(request.data.decode())
        api = init_dpapi(request.args)
        handler = api.http_handler.create(json_data["name"], json_data["local_address"], json_data["local_port"], json_data["state"], json_data["allowed_features"])
        return success_response('HTTP Handler "' + handler["name"] + '" was created')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@app.route("/api/mpgw/create", methods=['post'])
def create_mpgw():
    try:
        json_data, api = ast.literal_eval(request.data.decode()), init_dpapi(request.args)
        mpgw_name = json_data["mpgw_name"]
        policy = create_style_policy(json_data["rules"], mpgw_name, api=api)  
        api.mpgw.create(mpgw_name, front_handlers=json_data["handlers"], xml_manager="default", style_policy=policy["name"], state="enabled")
        return success_response('mpgw "' + mpgw_name + '" was created')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@app.route("/api/mpgw/update", methods=['post'])
def update_mpgw_policy():
    try:
        json_data = ast.literal_eval(request.data.decode())
        api = init_dpapi(request.args) 
        mpgw_obj = api.mpgw.get(json_data["mpgw_name"]) 

        # update policy
        policy_obj = api.style_policy.get(mpgw_obj["StylePolicy"]["value"])
        update_policy(json_data["rules"], policy_obj, api=api)

        # update handlers
        if json_data.get("handlers"):
            handlers = append_handlers(mpgw_obj["FrontProtocol"], json_data["handlers"])
            api.mpgw.update(mpgw_obj, FrontProtocol=handlers)
        
        return success_response('mpgw "' + json_data["mpgw_name"] + '" was updated')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@app.route("/api/mpgw/add_handlers", methods=['post'])
def add_handlers():
    try:
        json_data = ast.literal_eval(request.data.decode())
        api = init_dpapi(request.args) 
        mpgw_obj = api.mpgw.get(json_data["mpgw_name"]) 
        handlers = append_handlers(mpgw_obj["FrontProtocol"], json_data["handlers"])
        api.mpgw.update(mpgw_obj, FrontProtocol=handlers)
        return success_response('mpgw "' + json_data["mpgw_name"] + '" was updated')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)

   

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=4000, debug=True)
