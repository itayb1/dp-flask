#!/usr/bin/env python3

from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from apiwrapper import dpAPI
import json
import ast
from apiwrapper.exceptions import ApiError


app = Flask(__name__)
api = dpAPI.DpAPI("https://0.0.0.0:5554/", ("admin", "admin"), "default")
CORS(app)


@app.errorhandler(ApiError)
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
        if request.method == "POST":
            data_dict, handlers = ast.literal_eval(request.data.decode()), []
            if isinstance(data_dict, list):
                for handler_obj in data_dict:
                    handler = api.mq_handler.create(handler_obj["name"], handler_obj["queue_manager"], handler_obj["get_queue"], handler_obj["state"]) 
                    handlers.append(handler["name"])
            else:       
                handler = api.mq_handler.create(data_dict["name"], data_dict["queue_manager"], data_dict["get_queue"], data_dict["state"])
                return success_response('MQ Handler "' + handler["name"] + '" was created')
            return success_response('MQ Handlers ' + str(handlers).strip('[]') + ' were created')
    except ApiError as e:
        raise ApiError(e.message, e.status_code)


@app.route("/api/http_handler/create", methods=['post'])
def create_http_handler():
    try:
        if request.method == "POST":
            data_dict = ast.literal_eval(request.data.decode())
            handler = api.http_handler.create(data_dict["name"], data_dict["local_address"], data_dict["local_port"], data_dict["state"], data_dict["allowed_features"])
            return success_response('HTTP Handler "' + handler["name"] + '" was created')
    except ApiError as e:
        raise ApiError(e.message, e.status_code)


@app.route("/api/mpgw/create", methods=['post'])
def create_mpgw():
    try:
        data_dict = ast.literal_eval(request.data.decode())
        mpgw_name = data_dict["mpgw_name"]
        policy = create_style_policy(data_dict["rules"], mpgw_name)  
        api.mpgw.create(mpgw_name, front_handlers=data_dict["handlers"], xml_manager="default", style_policy=policy["name"], state="enabled")
        return success_response('mpgw "' + mpgw_name + '" was created')
    except ApiError as e:
        raise ApiError(e.message, e.status_code)


def create_action(type, fields, rule_name):
     if action["type"] == "validate":
        return create_validate_action(rule_name=rule_name, schema_url=fields["schema_url"], schema_type=fields["schema_type"])
    elif action["type"] == "xform":
        return create_transform_action(rule_name=rule_name, stylesheet_path=fields["stylesheet_path"], stylesheet_parameters=fields.get("stylesheet_parameters"))
    elif action["type"] == "gatewayscript":
        return create_gateway_script_action(rule_name=rule_name, gateway_script_path=fields["gateway_script_path"])
    elif action["type"] == "results":
        return create_results_action(rule_name=rule_name)
    else:
        raise ApiError("Invalid action type", 400) 


def create_rule_actions(rule_name, actions):
    try:
        rule_actions = []
        for action in actions:
            dp_action = create_action(action["type"], action["parameters"], rule_name)
            rule_actions.append(dp_action["name"])
        return rule_actions
    except ApiError as e:
        raise ApiError(e.message, e.status_code)


def create_style_policy(rules, mpgw_name):
    try:
        policy_maps = []
        for rule in rules:
            rule_name = rule["name"]
            rule_actions = create_rule_actions(rule_name, rule["actions"])        
            match_action = rule["match"]
            match_action = api.matching.create(name=match_action["name"],match_rules=match_action["match_rules"], combine_with_or=match_action["combine_with_or"], match_with_pcre=match_action["match_with_pcre"])
            policy_maps.append((match_action["name"], rule_name))
            api.rule.create(rule_name, direction=rule["direction"], actions=rule_actions)
        policy = api.style_policy.create(name="", policy_maps=policy_maps, mpgw=mpgw_name)
        return policy
    except ApiError as e:
        raise ApiError(e.message, e.status_code)
    

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=4000, debug=True)
