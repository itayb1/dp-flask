from flask import Blueprint, request, Response, jsonify
from utils import init_dpapi, exceptions, create_lbg
from utils.response_utils import success_response, handle_error

lbg_api = Blueprint('lbg_api', __name__)
lbg_api.register_error_handler(exceptions.ApiError, handle_error)


@lbg_api.route("/api/lbg", methods=['post'])
def create_load_balncer_group():
    try:
        api = init_dpapi(request.args)
        lbg_req = request.get_json(force=True)
        create_lbg(lbg_req, api)
        return success_response("Load Balancer Group {} was created successfully".format(lbg_req["name"]))
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)
