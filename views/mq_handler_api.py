from flask import Blueprint, request, Response
from utils import init_dpapi, exceptions
from utils.response_utils import success_response, handle_error
from utils.validations import validate_mq_handler

mq_handler_api = Blueprint('mq_handler_api', __name__)
mq_handler_api.register_error_handler(exceptions.ApiError, handle_error)


@mq_handler_api.route("/api/mq_handler", methods=['post'])
def create_mq_handler():
    try:
        errors = validate_mq_handler(request)
        if errors is not None:
            raise exceptions.ApiError(errors, 400)
        json_data = request.get_json(force=True)
        handlers = []
        api = init_dpapi(request.args)
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


@mq_handler_api.route("/api/mq_handler", methods=['get'])
def get_mq_handlers():
    try:
        api = init_dpapi(request.args)
        mq_handlers = api.mq_handler.get_all()
        return success_response(mq_handlers)
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@mq_handler_api.route("/api/mq_handler/<string:name>", methods=['get'])
def get_mq_handler(name):
    try:
        api = init_dpapi(request.args)
        mq_handler = api.mq_handler.get(name)
        return success_response(mq_handler)
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)
