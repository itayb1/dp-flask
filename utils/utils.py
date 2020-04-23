from dpAPI import DpAPI, exceptions
from copy import deepcopy
from flask import jsonify
from config.clusters import *
from config.secrets import clusters_creds


def get_cluster_data(cluster_name, cluster_type):
    clusters = prod_clusters if cluster_type == "prod" else test_clusters
    return clusters.get(cluster_name)


def get_cluster_creds(cluster_name, cluster_type):
    cluster_creds = clusters_creds.get(cluster_name)
    if cluster_creds:
        creds = cluster_creds.get(cluster_type)
        return creds
    return cluster_creds


def init_dpapi_from_cluster(cluster_data, cluster_creds):
    host = cluster_data["nodes"][0]["host"]
    port = cluster_data["nodes"][0]["port"]
    domain = cluster_data["domain"]
    return DpAPI(base_url="https://{}:{}/".format(host, port), auth=cluster_creds, domain=domain)


def init_dpapi_server(host, port, cluster_creds, domain):
    return DpAPI(base_url="https://{}:{}/".format(host, port), auth=cluster_creds, domain=domain)


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
            if uids.get(action["Type"]) == None:
                uids[action["Type"]] = 0
            action_name = api.action.create_name_by_convention(rule_name, action["Type"], uids[action["Type"]])
            dp_action = api.action.create_from_dict(action_name, fields=action, Type=action["Type"])
            rule_actions.append(dp_action["name"])
            uids[action["Type"]] += 1
        return rule_actions
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


def __update_rule_actions(rule_name, actions, api):
    try:
        rule_actions, uids = [], {}
        for action in actions:
            if uids.get(action["Type"]) == None:
                uids[action["Type"]] = 0
            action_name = api.action.create_name_by_convention(rule_name, action["Type"], uids[action["Type"]])
            dp_action = api.action.update_from_dict(action_name, fields=action, Type=action["Type"])
            rule_actions.append(dp_action["name"])
            uids[action["Type"]] += 1
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
            match_action = api.matching.create_from_dict(str(rule_name) + "_Match", fields=match_action)
            policy_maps.append((match_action["name"], rule_name))
            api.rule.create(rule_name, direction=rule["direction"], actions=rule_actions)
        return api.style_policy.create(name="", policy_maps=policy_maps, mpgw=mpgw_name)
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


def update_style_policy(rules, policy, api):
    try:
        policy_maps = deepcopy(policy["PolicyMaps"])
        if isinstance(policy_maps, dict):
            policy_maps = [policy_maps]
        rules_names = api.style_policy.get_rules_names(policy["name"])
        for rule in rules:
            rule_actions = __update_rule_actions(rule["name"], rule["actions"], api)
            match_action = rule["match"]
            api.matching.update_from_dict(str(rule["name"])  + "_Match", fields=match_action)
            policy_maps.append({"Match": {"value": match_action["name"]}, "Rule": {"value": rule["name"]}})
            if not (rule["name"] in rules_names):
                api.rule.create(rule["name"], direction=rule["direction"], actions=rule_actions)
        api.style_policy.update(policy, PolicyMaps=policy_maps)
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)


def create_xml_manager(mpgw_name, api):
    try:
        xml_manager_name = "{}_XMLManager".format(mpgw_name)
        api.xml_manager.create(xml_manager_name, virtual_servers=[lbg["name"] for lbg in  api.lbg.get_all()])
        return xml_manager_name
    except exceptions.ApiError as e:
        raise exceptions.ApiError(e.message, e.status_code)   


def create_lbg(lbg_req, api):
    health = lbg_req["healtcheck"]
    if health.get("type") == "Standard":
        api.lbg.create(lbg_req["name"], lbg_req["algorithm"], lbg_req["members"], healthcheck_type="Standard", healthcheck_port=health.get(
            "port"), healthcheck_uri=health.get("uri"), healthcheck_method=health.get("Method"))
    elif health.get("type") == "TCPConnection":
        api.lbg.create(lbg_req["name"], lbg_req["algorithm"], lbg_req["members"], healthcheck_type="TCPConnection", healthcheck_port=health.get("port"))
    else:
        raise exceptions.ApiError("Not a valid healthcheck type. Either TCPConnection or Standard", 400)


def append_handlers(current_handlers, new_handlers):
    handlers = deepcopy(current_handlers)
    handlers = [handlers] if isinstance(handlers, dict) else handlers
    [handlers.append({"value": handler}) for handler in new_handlers]
    return handlers
