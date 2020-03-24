from flask import Blueprint, request, Response, jsonify
from utils import init_dpapi, exceptions
from utils.response_utils import success_response, handle_error
from config.clusters import prod_clusters, test_clusters


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


@status_api.route("/api/status/cluster/<string:name>/<string:cluster_type>", methods=['get'])
def get_cluster_data(name, cluster_type):
    cluster = ""
    if cluster_type == "prod":
        cluster = prod_clusters.get(name)
    elif cluster_type == "test":
        cluster = test_clusters.get(name)
    else:
        raise exceptions.ApiError("Not a valid cluster type", 400)

    if cluster == None:
        raise exceptions.ApiError("Cluster not found", 404)

    return cluster


@status_api.route("/api/status/cluster/<string:cluster_type>", methods=['get'])
def get_cluster_names(cluster_type):
    if cluster_type == "prod":
        return jsonify(list(prod_clusters.keys()))
    elif cluster_type == "test":
        return jsonify(list(test_clusters.keys()))
    else:
        raise exceptions.ApiError("Not a valid cluster type", 400)