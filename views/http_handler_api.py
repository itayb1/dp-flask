from flask import Blueprint, request, Response
from utils import init_dpapi, exceptions
from utils.response_utils import success_response, handle_error
from utils.validations import validate_http_handler

http_handler_api = Blueprint('http_handler_api', __name__)
http_handler_api.register_error_handler(exceptions.ApiError, handle_error)


@http_handler_api.route("/api/http_handler", methods=['post'])
def create_http_handler():
    try:
        errors = validate_http_handler(request)
        if errors is not None:
            raise exceptions.ApiError(errors, 400)
        json_data = request.get_json(force=True)
        api = init_dpapi(request.args)
        handler = api.http_handler.create(json_data["name"], json_data["local_address"],
                                          json_data["local_port"], json_data["state"], json_data["allowed_features"])
        return success_response('HTTP Handler "' + handler["name"] + '" was created')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@http_handler_api.route("/api/http_handler", methods=['get'])
def get_http_handlers():
    try:
        api = init_dpapi(request.args)
        http_handlers = api.http_handler.get_all()
        return success_response(http_handlers)
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@http_handler_api.route("/api/http_handler/<string:name>", methods=['get'])
def get_http_handler(name):
    try:
        api = init_dpapi(request.args)
        http_handler = api.http_handler.get(name)
        return success_response(http_handler)
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)
