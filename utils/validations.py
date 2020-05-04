from flask_inputs import Inputs
from flask_inputs.validators import JsonSchema
from utils import exceptions
from config.environments import *


def validate_handlers_exists(api, handlers):
    for handler in handlers:
        try:
            http_handler = api.http_handler.get(handler)
        except Exception as e:
            try:
                mq_handler = api.mq_handler.get(handler)
            except Exception as e:
                if e.status_code == 404:
                    raise exceptions.ApiError(
                        "One of the provided handlers doesn't exist.", 400)
    return True


def is_policy_rules_exist(api, rules):
    for rule in rules:
        try:
            rule = api.rule.get(rule["name"])
            if rule:
                raise exceptions.ApiError(
                    "One of the provided rules already exists exist.", 409)
        except Exception as e:
            if e.status_code == 409:
                raise exceptions.ApiError(e.message, 409)
    return True


def validate_mpgw_name_is_free(api, name):
    try:
        mpgw = api.mpgw.get(name)
        if mpgw:
            raise exceptions.ApiError(
                "MultiProtoclGateway name is already taken", 409)
    except Exception as e:
        if e.status_code == 409:
            raise exceptions.ApiError(e.message, 409)
    return True


def __validate_handler_params(api, ip=None, port=None, queue_manager=None, cluster_name=None, cluster_type=None):
    if port:
        return api.status.is_port_free(int(port), ip)
    if queue_manager:
        qms = [qm["name"] for qm in api.mqqm.get_all()]
        if (queue_manager in qms):
            return True
        else:
            envs = prod_environments if cluster_type == "prod" else test_environments
            envs_in_cluster = envs.get(cluster_name)
            if envs_in_cluster and (queue_manager in envs_in_cluster.keys()):
                return True
    return False


def validate_policy_handlers(api, rules, cluster_name, cluster_type):
    for rule in rules:
        protocol = str(rule.srcAddr.protocol).lower()
        if protocol == "http":
            if not (__validate_handler_params(api, ip=rule.srcAddr.primaryAddress, port=rule.srcAddr.secondaryAddress)):
                raise exceptions.ApiError("source port {} is already taken".format(rule.srcAddr.secondaryAddress), 409)
        elif protocol == "mq":
            if not (__validate_handler_params(api, queue_manager=rule.srcAddr.primaryAddress, cluster_name=cluster_name, cluster_type=cluster_type)):
                raise exceptions.ApiError("queue manager {} is not valid".format(rule.srcAddr.primaryAddress), 400)
        else:
            raise exceptions.ApiError("front handler protocol is not valid", 400)

    return True


def validate_mpgw_request(api, mpgw_reg):
    validate_mpgw_name_is_free(api, mpgw_reg["name"])
    validate_handlers_exists(api, mpgw_reg["handlers"])
    is_policy_rules_exist(api, mpgw_reg["rules"])
