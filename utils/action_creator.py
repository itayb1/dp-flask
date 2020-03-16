from dpAPI import exceptions


def create_action_based_on_type(api, action_type, action_json, rule_name, uid):
    action_funcs = {"validate": __create_validate_action, "xform": __create_xform_action,
                    "gatewayscript": __create_gatewayscript_action, "results": __create_results_action}
    if action_type in action_funcs.keys():
        return action_funcs[action_type](api, action_json, rule_name, uid)
    else:
        raise exceptions.ApiError("Invalid action type", 400)


def __create_validate_action(api, action_json, rule_name, uid):
    fields = action_json["parameters"]
    return api.action.create_validate_action(rule_name=rule_name, schema_url=fields["schema_url"], schema_type=fields["schema_type"], uid=uid, Input=fields["input"], Output=fields["output"])


def __create_xform_action(api, action_json, rule_name, uid):
    fields = action_json["parameters"]
    return api.action.create_transform_action(rule_name=rule_name, stylesheet_path=fields["stylesheet_path"], stylesheet_parameters=fields.get("stylesheet_parameters"), uid=uid, Input=fields["input"], Output=fields["output"])


def __create_gatewayscript_action(api, action_json, rule_name, uid):
    fields = action_json["parameters"]
    return api.action.create_gateway_script_action(rule_name=rule_name, gateway_script_path=fields["gateway_script_path"], uid=uid, Input=fields["input"], Output=fields["output"])


def __create_results_action(api, action_json, rule_name, uid):
    fields = action_json["parameters"]
    return api.action.create_results_action(rule_name=rule_name, uid=uid, Input=fields["input"])
