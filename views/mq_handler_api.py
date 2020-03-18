from flask import Blueprint, request, Response, jsonify
from utils import init_dpapi, exceptions
from utils.response_utils import success_response, handle_error
from utils.validations import validate_mq_handler

mq_handler_api = Blueprint('mq_handler_api', __name__)
mq_handler_api.register_error_handler(exceptions.ApiError, handle_error)


@mq_handler_api.route("/api/mq_handler", methods=['post'])
def create_mq_handler():
    try:
        json_data = request.get_json(force=True)
        handlers = []
        api = init_dpapi(request.args)
        if isinstance(json_data, list):
            for handler_obj in json_data:
                api.mq_handler.create_from_dict(handler_obj["name"], fields=handler_obj)
                handlers.append(handler_obj["name"])
        else:
            api.mq_handler.create_from_dict(json_data["name"], fields=json_data)
            return success_response('MQ Handler "' + json_data["name"] + '" was created')
        return success_response('MQ Handlers ' + str(handlers).strip('[]') + ' were created')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@mq_handler_api.route("/api/mq_handler", methods=['put'])
def update_mq_handler():
    try:
        json_data = request.get_json(force=True)
        handlers = []
        api = init_dpapi(request.args)
        if isinstance(json_data, list):
            for handler_obj in json_data:
                api.mq_handler.update_from_dict(handler_obj["name"], fields=handler_obj)
                handlers.append(handler_obj["name"])
        else:
            api.mq_handler.update_from_dict(json_data["name"], fields=json_data)
            return success_response('MQ Handler "' + json_data["name"] + '" was updated')
        return success_response('MQ Handlers ' + str(handlers).strip('[]') + ' were updated')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@mq_handler_api.route("/api/mq_handler", methods=['get'])
def get_mq_handlers():
    try:
        api = init_dpapi(request.args)
        mq_handlers = api.mq_handler.get_all()
        return jsonify(mq_handlers)
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


@mq_handler_api.route("/api/mq_handler/<string:name>", methods=['get'])
def get_mq_handler(name):
    try:
        api = init_dpapi(request.args)
        mq_handler = api.mq_handler.get(name)
        return jsonify(mq_handler)
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)
