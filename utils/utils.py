from dpAPI import DpAPI, exceptions
from copy import deepcopy
from flask import jsonify


def init_dpapi(query_string):
    host = query_string.get("host")
    port = query_string.get("port")
    username = query_string.get("username")
    password = query_string.get("password")
    domain = query_string.get("domain")
    return DpAPI(base_url="https://{}:{}/".format(host, port), auth=(username, password), domain=domain)


def __create_rule_actions(rule_name, actions, api):
    try:
        rule_actions, uids = [], {}
        for action in actions:
            if uids.get(action["type"]) == None:
                uids[action["type"]] = 0
            action_name = api.action.create_name_by_convention(rule_name, action["type"], uids[action["type"]])
            dp_action = api.action.create_from_dict(action_name, fields=action["parameters"], Type=action["type"])
            rule_actions.append(dp_action["name"])
            uids[action["type"]] += 1
        return rule_actions
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


def update_policy(rules, policy, api):
    try:
        policy_maps = deepcopy(policy["PolicyMaps"])
        if isinstance(policy_maps, dict):
            policy_maps = [policy_maps]

        for rule in rules:
            rule_actions = __create_rule_actions(rule["name"], rule["actions"], api)
            match_action = rule["match"]
            api.matching.create_from_dict(match_action["name"], fields=match_action)
            policy_maps.append({"Match": {"value": match_action["name"]}, "Rule": {"value": rule["name"]}})
            api.rule.create(rule["name"], direction=rule["direction"], actions=rule_actions)
        api.style_policy.update(policy, PolicyMaps=policy_maps)
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


def create_style_policy(rules, mpgw_name, api):
    try:
        policy_maps = []
        for rule in rules:
            rule_name = rule["name"]
            rule_actions = __create_rule_actions(rule_name, rule["actions"], api)
            match_action = rule["match"]
            match_action = api.matching.create_from_dict(match_action["name"], fields=match_action)
            policy_maps.append((match_action["name"], rule_name))
            api.rule.create(rule_name, direction=rule["direction"], actions=rule_actions)
        policy = api.style_policy.create(name="", policy_maps=policy_maps, mpgw=mpgw_name)
        return policy
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


def append_handlers(current_handlers, new_handlers):
    handlers = deepcopy(current_handlers)
    [handlers.append({"value": handler}) for handler in new_handlers]
    return handlers
