from flask import Blueprint, request, Response, jsonify
from utils import create_style_policy, init_dpapi, exceptions, update_policy, append_handlers
from utils.response_utils import success_response, handle_error
from utils.validations import validate_handlers_exists

mpgw_api = Blueprint('mpgw_api', __name__)
mpgw_api.register_error_handler(exceptions.ApiError, handle_error)


@mpgw_api.route("/api/mpgw", methods=['post'])
def create_mpgw():
    try:
        api = init_dpapi(request.args)
        mpgw_req = request.get_json(force=True)
        validate_handlers_exists(api, mpgw_req["handlers"])
        policy = create_style_policy(mpgw_req["rules"], mpgw_req["name"], api=api)
        api.mpgw.create(mpgw_req["name"], mpgw_req["handlers"], "default", policy["name"], state="enabled")
        return success_response('mpgw "' + mpgw_req["name"] + '" was created')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@mpgw_api.route("/api/mpgw", methods=['put'])
def update_mpgw_policy():
    try:
        mpgw_req = request.get_json(force=True)
        api = init_dpapi(request.args)
        mpgw_obj = api.mpgw.get(mpgw_req["name"])

        # update policy
        policy_obj = api.style_policy.get(mpgw_obj["StylePolicy"]["value"])
        update_policy(mpgw_req["rules"], policy_obj, api=api)

        # update handlers
        if mpgw_req.get("handlers"):
            handlers = append_handlers(mpgw_obj["FrontProtocol"], mpgw_req["handlers"])
            api.mpgw.update(mpgw_obj, FrontProtocol=handlers)

        return success_response('mpgw "' + mpgw_req["name"] + '" was updated')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@mpgw_api.route("/api/mpgw/add_handlers", methods=['post'])
def add_handlers():
    try:
        json_data = request.get_json(force=True)
        api = init_dpapi(request.args)
        mpgw_obj = api.mpgw.get(json_data["name"])
        handlers = append_handlers(
            mpgw_obj["FrontProtocol"], json_data["handlers"])
        api.mpgw.update(mpgw_obj, FrontProtocol=handlers)
        return success_response('mpgw "' + json_data["name"] + '" was updated')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)
    except Exception as e:
        raise exceptions.ApiError("Something is wrong dude", 500)


@mpgw_api.route("/api/mpgw", methods=['get'])
def get_mpgws():
    try:
        api = init_dpapi(request.args)
        mpgws = api.mpgw.get_all()
        return jsonify([mpgw["name"] for mpgw in mpgws])
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@mpgw_api.route("/api/mpgw/<string:name>", methods=['get'])
def get_mpgw(name):
    try:
        api = init_dpapi(request.args)
        rules, handlers = [], []
        resp_mpgw = api.mpgw.get(name)
        policy_maps = api.style_policy.get(resp_mpgw["StylePolicy"]["value"])["PolicyMaps"]
        policy_maps = [policy_maps] if isinstance(policy_maps, dict) else policy_maps
        for policy_map in policy_maps:   
            resp_rule = api.rule.get(policy_map["Rule"]["value"])
            rules.append({"name": policy_map["Rule"]["value"], "direction": resp_rule["Direction"], "actions": [api.action.get(
                action["value"]) for action in resp_rule["Actions"]], "match": api.matching.get(policy_map["Match"]["value"])})
                
        if isinstance(resp_mpgw["FrontProtocol"], dict):
            handlers.append(resp_mpgw["FrontProtocol"]["value"])
        elif isinstance(resp_mpgw["FrontProtocol"], list):
            for handler in resp_mpgw["FrontProtocol"]:
                handlers.append(handler["value"])

        return {   
            "name": name,
            "rules": rules,
            "handlers": handlers
        }
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)