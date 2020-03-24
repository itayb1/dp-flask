from flask_inputs import Inputs
from flask_inputs.validators import JsonSchema
from utils import exceptions


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


def validate_mpgw_request(api, mpgw_reg):
    validate_mpgw_name_is_free(api, mpgw_reg["name"])
    validate_handlers_exists(api, mpgw_reg["handlers"])
    is_policy_rules_exist(api, mpgw_reg["rules"])
