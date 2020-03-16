from dpAPI import DpAPI, exceptions
from copy import deepcopy
from flask import jsonify
from .action_creator import create_action_based_on_type


def __create_action(action_type, action_json, rule_name, uid, api):
    try:
        return create_action_based_on_type(api, action_type, action_json, rule_name, uid)
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


def __create_rule_actions(rule_name, actions, api):
    try:
        rule_actions, uids = [], {}
        for action in actions:
            if uids.get(action["type"]) == None:
                uids[action["type"]] = 0
            dp_action = __create_action(
                action["type"], action, rule_name, uids[action["type"]], api=api)
            rule_actions.append(dp_action["name"])
            uids[action["type"]] += 1
        return rule_actions
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


def init_dpapi(query_string):
    host = query_string.get("host")
    port = query_string.get("port")
    username = query_string.get("username")
    password = query_string.get("password")
    domain = query_string.get("domain")
    return DpAPI(base_url="https://{}:{}/".format(host, port), auth=(username, password), domain=domain)


def append_handlers(current_handlers, new_handlers):
    handlers = deepcopy(current_handlers)
    [handlers.append({"value": handler}) for handler in new_handlers]
    return handlers


def update_policy(rules, policy, api):
    try:
        policy_maps = deepcopy(policy["PolicyMaps"])
        if isinstance(policy_maps, dict):
            policy_maps = [policy_maps]

        for rule in rules:
            rule_actions = __create_rule_actions(
                rule["name"], rule["actions"], api)
            match_action = rule["match"]
            api.matching.create(name=match_action["name"], match_rules=match_action["match_rules"],
                                combine_with_or=match_action["combine_with_or"], match_with_pcre=match_action["match_with_pcre"])
            policy_maps.append(
                {"Match": {"value": match_action["name"]}, "Rule": {"value": rule["name"]}})
            api.rule.create(
                rule["name"], direction=rule["direction"], actions=rule_actions)
        api.style_policy.update(policy, PolicyMaps=policy_maps)
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


def create_style_policy(rules, mpgw_name, api):
    try:
        policy_maps = []
        for rule in rules:
            rule_name = rule["name"]
            rule_actions = __create_rule_actions(
                rule_name, rule["actions"], api)
            match_action = rule["match"]
            match_action = api.matching.create(name=match_action["name"], match_rules=match_action["match_rules"],
                                               combine_with_or=match_action["combine_with_or"], match_with_pcre=match_action["match_with_pcre"])
            policy_maps.append((match_action["name"], rule_name))
            api.rule.create(
                rule_name, direction=rule["direction"], actions=rule_actions)
        policy = api.style_policy.create(
            name="", policy_maps=policy_maps, mpgw=mpgw_name)
        return policy
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)
