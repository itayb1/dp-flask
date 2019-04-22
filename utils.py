from apiwrapper import dpAPI

def create_action(type, fields, rule_name):
     if action["type"] == "validate":
        return create_validate_action(rule_name=rule_name, schema_url=fields["schema_url"], schema_type=fields["schema_type"])
    elif action["type"] == "xform":
        return create_transform_action(rule_name=rule_name, stylesheet_path=fields["stylesheet_path"], stylesheet_parameters=fields.get("stylesheet_parameters"))
    elif action["type"] == "gatewayscript":
        return create_gateway_script_action(rule_name=rule_name, gateway_script_path=fields["gateway_script_path"])
    elif action["type"] == "results":
        return create_results_action(rule_name=rule_name)
    else:
        raise ApiError("Invalid action type", 400) 


def create_rule_actions(rule_name, actions):
    try:
        rule_actions = []
        for action in actions:
            dp_action = create_action(action["type"], action["parameters"], rule_name)
            rule_actions.append(dp_action["name"])
        return rule_actions
    except ApiError as e:
        raise ApiError(e.message, e.status_code)


def create_style_policy(rules, mpgw_name):
    try:
        policy_maps = []
        for rule in rules:
            rule_name = rule["name"]
            rule_actions = create_rule_actions(rule_name, rule["actions"])        
            match_action = rule["match"]
            match_action = api.matching.create(name=match_action["name"],match_rules=match_action["match_rules"], combine_with_or=match_action["combine_with_or"], match_with_pcre=match_action["match_with_pcre"])
            policy_maps.append((match_action["name"], rule_name))
            api.rule.create(rule_name, direction=rule["direction"], actions=rule_actions)
        policy = api.style_policy.create(name="", policy_maps=policy_maps, mpgw=mpgw_name)
        return policy
    except ApiError as e:
        raise ApiError(e.message, e.status_code)