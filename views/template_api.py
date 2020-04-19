from flask import Blueprint, request, Response, jsonify
from utils import create_style_policy, init_dpapi, exceptions, update_style_policy, append_handlers, create_xml_manager
from utils.response_utils import success_response, handle_error
from utils.validations import validate_mpgw_request
from utils.template_utils import  populate_mpgw_template
from copy import deepcopy  

template_api = Blueprint('template_api', __name__)
template_api.register_error_handler(exceptions.ApiError, handle_error)


@template_api.route("/api/template/mpgw", methods=['post'])
def create_mpgw_from_template():
    try:
        api = init_dpapi(request.args)
        req = request.get_json(force=True)
        mpgw = populate_mpgw_template(req, api)
        xml_manager_name = create_xml_manager(mpgw["name"], api)
        policy = create_style_policy(mpgw["rules"], mpgw["name"], api=api)
        api.mpgw.create(mpgw["name"], mpgw["handlers"], xml_manager_name, policy["name"], state="enabled", UserSummary=str(req))
        return success_response('MultiProtocolGateway "' + mpgw["name"] + '" was created')
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)



