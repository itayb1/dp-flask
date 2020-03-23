from flask import Blueprint, request, Response, jsonify
from utils import init_dpapi, exceptions
from utils.response_utils import success_response, handle_error

status_api = Blueprint('status_api', __name__)
status_api.register_error_handler(exceptions.ApiError, handle_error)


@status_api.route("/api/status/port", methods=['get'])
def get_free_port():
    try:
        api = init_dpapi(request.args)
        return success_response(api.status.get_free_port())
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@status_api.route("/api/status/port/<int:port>", methods=['get'])
def is_free_port(port):
    try:
        api = init_dpapi(request.args)
        return success_response(api.status.is_port_free(port))
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)