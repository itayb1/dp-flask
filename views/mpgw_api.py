from flask import Blueprint, request, Response
from utils import create_style_policy, init_dpapi, exceptions, update_policy, append_handlers
from utils.response_utils import success_response, handle_error

mpgw_api = Blueprint('mpgw_api', __name__)
mpgw_api.register_error_handler(exceptions.ApiError, handle_error)


@mpgw_api.route("/api/mpgw", methods=['post'])
def create_mpgw():
    try:
        json_data = request.get_json(force=True)
        api = init_dpapi(request.args)
        mpgw_name = json_data["mpgw_name"]
        policy = create_style_policy(json_data["rules"], mpgw_name, api=api)
        api.mpgw.create(mpgw_name, front_handlers=json_data["handlers"],
                        xml_manager="default", style_policy=policy["name"], state="enabled")
        return success_response('mpgw "' + mpgw_name + '" was created')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@mpgw_api.route("/api/mpgw", methods=['put'])
def update_mpgw_policy():
    try:
        json_data = request.get_json(force=True)
        api = init_dpapi(request.args)
        mpgw_obj = api.mpgw.get(json_data["mpgw_name"])

        # update policy
        policy_obj = api.style_policy.get(mpgw_obj["StylePolicy"]["value"])
        update_policy(json_data["rules"], policy_obj, api=api)

        # update handlers
        if json_data.get("handlers"):
            handlers = append_handlers(
                mpgw_obj["FrontProtocol"], json_data["handlers"])
            api.mpgw.update(mpgw_obj, FrontProtocol=handlers)

        return success_response('mpgw "' + json_data["mpgw_name"] + '" was updated')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@mpgw_api.route("/api/mpgw/add_handlers", methods=['post'])
def add_handlers():
    try:
        json_data = request.get_json(force=True)
        api = init_dpapi(request.args)
        mpgw_obj = api.mpgw.get(json_data["mpgw_name"])
        handlers = append_handlers(
            mpgw_obj["FrontProtocol"], json_data["handlers"])
        api.mpgw.update(mpgw_obj, FrontProtocol=handlers)
        return success_response('mpgw "' + json_data["mpgw_name"] + '" was updated')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)
    except Exception as e:
        raise exceptions.ApiError("Something is wrong dude", 500)
