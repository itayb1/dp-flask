from config.templates import *
from copy import deepcopy
from config.environments import prod_environments, test_environments
from utils.validations import *
import numpy as np
from jinja2 import Template
import json, ast


def get_environments(cluster_name, cluster_type):
    envs = prod_environments if cluster_type == "prod" else test_environments
    return envs.get(cluster_name)

def generate_mq_url_match(queue_manager, get_queue):
    return "dpmq://{queue_manager}/{front_handler}\?RequestQueue={get_queue}".format(queue_manager=queue_manager, front_handler=get_queue+"_FSH*", get_queue=get_queue)


def get_size_threshold_in_kb(file_size, unit):
    mul = {"mb": 1000, "gb": 1000000, "kb": 1}
    return file_size * mul[unit]


def create_filter_action(template, dpas_filter, schema_path, filter_type):
    filter_action = deepcopy(template)
    if filter_type == "schema":
        filter_action["SchemaURL"] = schema_path
    return filter_action


def create_slm_statements(template_var, slm_input):
    template = Template(json.dumps(template_var))
    slm_statement_size = json.loads(template.render(action="throttle", interval=slm_input["fileSizeTimeUnit"], intervalType="moving", thresholdAlgorithm="greater-than", thresholdType="payload-total", thresholdLevel=get_size_threshold_in_kb(slm_input["maxFileSize"], slm_input["fileSizeUnit"])))
    slm_statement_count = json.loads(template.render(action="throttle", interval=slm_input["fileCountTimeUnit"], intervalType="moving", thresholdAlgorithm="greater-than", thresholdType="count-all", thresholdLevel=slm_input["maxFileCount"]))
    return [slm_statement_size, slm_statement_count]


def create_destination_action(template_var, primary_address, secondary_address):
    template = Template(json.dumps(template_var))
    return json.loads(template.render(primaryAddress=primary_address, secondaryAddress=secondary_address))


def create_slm_action(template, rule, rule_name, api):
    if not (None in rule.get("slm").values()):
        slm_action = deepcopy(template)
        slm_policy = api.slm.create("{rule_name}_SLM_policy".format(rule_name=rule_name), create_slm_statements(slm_statement_template ,rule["slm"]))
        slm_action["SLMPolicy"] = slm_policy["name"]
        return slm_action
    return None


def create_match_rules(template, primary_address, secondary_address, protocol):
    match_rule = deepcopy(template)
    if protocol == "http":
        match_rule["Url"] = "http://{ip}:{port}*".format(ip=primary_address, port=secondary_address)
    elif protocol == "mq":
        match_rule["Url"] = generate_mq_url_match(primary_address, secondary_address)

    return match_rule


def create_rule_actions(template_var, filter_action, destination_action, slm_action=None):
    template = Template(json.dumps(template_var))
    rule_actions = json.loads(template.render(slm=slm_action, filter=filter_action, destination=destination_action))
    return [ast.literal_eval(str(action)) for action in rule_actions if action != "None"]


def __create_rule_handlers(primary_address, secondary_address, protocol, methods, rule_name, api, cluster_name, cluster_type):
    handlers = []
    if protocol == "http":
        handlers.append(api.http_handler.create("{rule_name}_HTTP_FSH".format(rule_name=rule_name), primary_address, secondary_address, "enabled", methods)["name"])
    elif protocol == "mq":
        envs = get_environments(cluster_name, cluster_type)
        if primary_address in envs.keys():
            for i, qm in enumerate(envs[primary_address]):
                handler = api.mq_handler.create("{queue_name}_FSH_{id}".format(queue_name=secondary_address, id=(i+1)), qm, secondary_address, "enabled")
                handlers.append(handler["name"])
        else:
            handlers.append(api.mq_handler.create("{queue_name}_FSH".format(queue_name=secondary_address), primary_address, secondary_address, "enabled")["name"])
    return handlers


def populate_mpgw_template(req, api):
    mpgw = deepcopy(mpgw_template)
    mpgw["name"] = req["details"]["projectNameValue"]
    cluster_type = req["details"]["testOrProd"]
    cluster_name = req["details"]["clusterName"]
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
                destination_action = create_destination_action(destination_templates[dest_protocol], dest_address["primaryAddress"], dest_address["secondaryAddress"])
                match["MatchRules"] = create_match_rules(match_rule_template, src_address["primaryAddress"], src_address["secondaryAddress"], src_prorocol)
                rule_obj["match"] = match
                rule_obj["actions"] = create_rule_actions(rule_actions_template, filter_action, destination_action, slm_action)
                mpgw["rules"].append(rule_obj)
                mpgw["handlers"] += __create_rule_handlers(src_address["primaryAddress"], src_address["secondaryAddress"], src_prorocol, src_address["methods"], rule_obj["name"], api, cluster_name, cluster_type)

        error_rule = deepcopy(error_rule_template)
        error_rule["name"] = mpgw["name"] + "_error_rule"
        mpgw["rules"].append(error_rule)
        return mpgw
