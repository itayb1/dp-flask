from config.templates import *
from copy import deepcopy
from config.environments import environments
from utils.validations import *
import numpy as np


def generate_mq_url_match(queue_manager, get_queue):
    return "dpmq://{queue_manager}/{front_handler}\?RequestQueue={get_queue}".format(queue_manager=queue_manager, front_handler=get_queue+"_FSH*", get_queue=get_queue)


def create_filter_action(template, dpas_filter, schema_path, filter_type):
    filter_action = deepcopy(template)
    if filter_type == "schema":
        filter_action["SchemaURL"] = schema_path

    return filter_action


def create_destination_action(template, primary_address, secondary_address, protocol):
    destination_action = deepcopy(template)
    if protocol == "http":
        destination_action["StylesheetParameters"][0]["ParameterValue"] = "http://{ip}:{port}".format(
            ip=primary_address, port=secondary_address)
    elif protocol == "mq":
        destination_action["StylesheetParameters"][0]["ParameterValue"] = primary_address
        destination_action["StylesheetParameters"][1]["ParameterValue"] = secondary_address

    return destination_action


def create_slm_action(template, rule, rule_name, api):
    if rule.get("slm") != None:
        slm_action = deepcopy(template)
        slm_policy = api.slm.create("{rule_name}_SLM_policy".format(
            rule_name=rule_name), rule["slm"]["statements"])
        slm_action["SLMPolicy"] = slm_policy["name"]
        return slm_action
    return None


def create_match_rules(template, primary_address, secondary_address, protocol):
    match_rule = deepcopy(template)
    if protocol == "http":
        match_rule["Url"] = "http://{ip}:{port}*".format(
            ip=primary_address, port=secondary_address)
    elif protocol == "mq":
        match_rule["Url"] = generate_mq_url_match(
            primary_address, secondary_address)

    return match_rule


def create_rule_actions(template, filter_action, destination_action, slm_action):
    rule_actions = deepcopy(template)
    if slm_action != None:
        rule_actions.insert(0, slm_action)
    np_array = np.array(rule_actions)
    np_array = np.where(np_array == "filter", filter_action, np_array)
    np_array = np.where(np_array == "destination",
                        destination_action, np_array)
    return list(np_array)


def __create_rule_handlers(primary_address, secondary_address, protocol, methods, rule_name, api):
    handler = []
    if protocol == "http":
        handler = api.http_handler.create("{rule_name}_HTTP_FSH".format(
            rule_name=rule_name), primary_address, secondary_address, "enabled", methods)
    elif protocol == "mq":
        if primary_address in environments.keys():
            handlers = []
            for i, qm in enumerate(environments[primary_address]):
                handler = api.mq_handler.create("{queue_name}_FSH_{id}".format(
                    queue_name=secondary_address, id=(i+1)), qm, secondary_address, "enabled")
                handlers.append(handler["name"])
            return handlers
        else:
            handler = api.mq_handler.create("{queue_name}_FSH".format(
                queue_name=secondary_address), primary_address, secondary_address, "enabled")
    return [handler["name"]]


def populate_mpgw_template(req, api):
    mpgw = deepcopy(mpgw_template)
    mpgw["name"] = req["details"]["projectNameValue"]
    if validate_mpgw_name_is_free(api, mpgw["name"]) != False:
        # Handling creation of mpgw policy rules
        for rule in req["rules"]:
            dest_protocol = rule["destAddr"]["protocol"].lower()
            src_prorocol = rule["srcAddr"]["protocol"].lower()
            filter_type = rule["filter"]["filterType"].lower()
            dest_address = rule["destAddr"]
            src_address = rule["srcAddr"]
            match = deepcopy(match_template)
            rule_obj = deepcopy(rule_template)
            rule_obj["name"] = "{mpgw}_{name}_rule".format(mpgw=mpgw["name"], name=rule["name"])

            # if rule doesn't exist, create rule's actions, match and associated handlers
            if is_policy_rule_exists(api, [rule_obj]) != False:
                slm_action = create_slm_action(slm_action_template, rule, rule_obj["name"], api)
                filter_action = create_filter_action(filters_templates[filter_type], rule["filter"]["dpasFilter"], rule["filter"]["schemaPath"], filter_type)
                destination_action = create_destination_action(destination_templates[dest_protocol], dest_address["primaryAddress"], dest_address["secondaryAddress"], dest_protocol)
                match["MatchRules"] = create_match_rules(match_rule_template, src_address["primaryAddress"], src_address["secondaryAddress"], src_prorocol)
                rule_obj["match"] = match
                rule_obj["actions"] = create_rule_actions(rule_actions_template, filter_action, destination_action, slm_action)
                mpgw["rules"].append(rule_obj)
                mpgw["handlers"] += __create_rule_handlers(src_address["primaryAddress"], src_address["secondaryAddress"], src_prorocol, src_address["methods"], rule_obj["name"], api)

        error_rule = deepcopy(error_rule_template)
        error_rule["name"] = mpgw["name"] + "_error_rule"
        mpgw["rules"].append(error_rule)
        return mpgw
