from flask import Blueprint, request, Response, jsonify
from utils import init_dpapi, exceptions, get_cluster_creds, get_cluster_data, init_dpapi_from_cluster
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


@mqqm_api.route("/api/mqqm/<string:cluster_name>/<string:cluster_type>", methods=['get'])
def get_mqqm_cluster(cluster_name, cluster_type):
    try:
        cluster_creds = get_cluster_creds(cluster_name, cluster_type)
        cluster_data = get_cluster_data(cluster_name, cluster_type)
        if cluster_creds and cluster_data:
            api = init_dpapi_from_cluster(cluster_data, cluster_creds)
            return jsonify([qm["name"] for qm in api.mqqm.get_all()])
        else:
            raise exceptions.ApiError("Not a valid cluster", 400)
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)

