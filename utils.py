from dpAPI import DpAPI, exceptions


def init_dpapi(query_string):
    dp = query_string.get("dp") + "/"
    username = query_string.get("username")
    password = query_string.get("password")
    domain = query_string.get("domain")
    return DpAPI(base_url=dp, auth=(username, password), domain=domain)


def __create_action(action_type, fields, rule_name, uid, api):
    if action_type == "validate":
        return api.action.create_validate_action(rule_name=rule_name, schema_url=fields["schema_url"], schema_type=fields["schema_type"], uid=uid, Input=fields["input"], Output=fields["output"])
    elif action_type == "xform":
        return api.action.create_transform_action(rule_name=rule_name, stylesheet_path=fields["stylesheet_path"], stylesheet_parameters=fields.get("stylesheet_parameters"), uid=uid, Input=fields["input"], Output=fields["output"])
    elif action_type == "gatewayscript":
        return api.action.create_gateway_script_action(rule_name=rule_name, gateway_script_path=fields["gateway_script_path"], uid=uid, Input=fields["input"], Output=fields["output"])
    elif action_type == "results":
        return api.action.create_results_action(rule_name=rule_name, uid=uid, Input=fields["input"])
    else:
        raise exceptions.ApiError("Invalid action type", 400) 


def __create_rule_actions(rule_name, actions, api):
    try:
        rule_actions, uids = [], {}
        for action in actions:
            if uids.get(action["type"]) == None:
                uids[action["type"]] = 0
            dp_action = __create_action(action["type"], action["parameters"], rule_name, uids[action["type"]], api=api)
            rule_actions.append(dp_action["name"])
            uids[action["type"]] += 1
        return rule_actions
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


def create_style_policy(rules, mpgw_name, api):
    try:
        policy_maps = []
        for rule in rules:
            rule_name = rule["name"]
            rule_actions = __create_rule_actions(rule_name, rule["actions"], api)        
            match_action = rule["match"]
            match_action = api.matching.create(name=match_action["name"],match_rules=match_action["match_rules"], combine_with_or=match_action["combine_with_or"], match_with_pcre=match_action["match_with_pcre"])
            policy_maps.append((match_action["name"], rule_name))
            api.rule.create(rule_name, direction=rule["direction"], actions=rule_actions)
        policy = api.style_policy.create(name="", policy_maps=policy_maps, mpgw=mpgw_name)
        return policy
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)