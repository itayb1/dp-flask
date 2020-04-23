from flask import Blueprint, request, Response, jsonify
from utils import init_dpapi, exceptions
from utils.response_utils import success_response, handle_error

mqqm_api = Blueprint('mqqm_api', __name__)
mqqm_api.register_error_handler(exceptions.ApiError, handle_error)


@mqqm_api.route("/api/mqqm", methods=['get'])
def get_mqqm():
    try:
        api = init_dpapi(request.args)
        return jsonify([qm["name"] for qm in api.mqqm.get_all()])
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)
