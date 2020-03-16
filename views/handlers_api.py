from flask import Blueprint, request, Response
from utils import init_dpapi, exceptions
from utils.response_utils import success_response, handle_error

handlers_api = Blueprint('handlers_api', __name__)
handlers_api.register_error_handler(exceptions.ApiError, handle_error)


@handlers_api.route("/api/mq_handler", methods=['post'])
def create_mq_handler():
    try:
        json_data, handlers, api = request.get_json(
            force=True), [], init_dpapi(request.args)
        if isinstance(json_data, list):
            for handler_obj in json_data:
                handler = api.mq_handler.create(
                    handler_obj["name"], handler_obj["queue_manager"], handler_obj["get_queue"], handler_obj["state"])
                handlers.append(handler["name"])
        else:
            handler = api.mq_handler.create(
                json_data["name"], json_data["queue_manager"], json_data["get_queue"], json_data["state"])
            return success_response('MQ Handler "' + handler["name"] + '" was created')
        return success_response('MQ Handlers ' + str(handlers).strip('[]') + ' were created')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@handlers_api.route("/api/http_handler", methods=['post'])
def create_http_handler():
    try:
        json_data = request.get_json(force=True)
        api = init_dpapi(request.args)
        handler = api.http_handler.create(json_data["name"], json_data["local_address"],
                                          json_data["local_port"], json_data["state"], json_data["allowed_features"])
        return success_response('HTTP Handler "' + handler["name"] + '" was created')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)
