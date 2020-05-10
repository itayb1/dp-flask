from config.templates import *
from copy import deepcopy
from config.environments import prod_environments, test_environments
from utils.validations import *
import numpy as np
from jinja2 import Template
import json, ast
from collections import namedtuple


def _json_object_hook(d): 
    return namedtuple('X', d.keys())(*d.values())


def json2obj(data): 
    return json.loads(data, object_hook=_json_object_hook)


def get_environments(cluster_name, cluster_type):
    envs = prod_environments if cluster_type == "prod" else test_environments
    return envs.get(cluster_name)


def generate_mq_url_match(queue_manager, get_queue):
    return "dpmq://{queue_manager}/{front_handler}\?RequestQueue={get_queue}".format(queue_manager=queue_manager, front_handler=get_queue+"_FSH*", get_queue=get_queue)


def get_size_threshold_in_kb(file_size, unit):
    mul = {"mb": 1000, "gb": 1000000, "kb": 1}
    return file_size * mul[unit]


def render_filter_action(template_var, dpas_filter, schema_path, filter_type, schema_type):
    if filter_type == "schema":
        template = Template(json.dumps(template_var["schema"][schema_type.lower()]))
        if schema_path.startswith("local:///"):
            return json.loads(template.render(schemaName=schema_path))
        else:
            return json.loads(template.render(schemaName="local:///{}".format(schema_path)))


def render_slm_statement(template_var, slm):
    template = Template(json.dumps(template_var))
    slm_statement_size = json.loads(template.render(action="throttle", interval=slm.fileSizeTimeUnit, intervalType="moving", thresholdAlgorithm="greater-than", thresholdType="payload-total", thresholdLevel=get_size_threshold_in_kb(slm.maxFileSize, slm.fileSizeUnit)))
    slm_statement_count = json.loads(template.render(action="throttle", interval=slm.fileCountTimeUnit, intervalType="moving", thresholdAlgorithm="greater-than", thresholdType="count-all", thresholdLevel=slm.maxFileCount))
    return [slm_statement_size, slm_statement_count]


def render_destination_action(template_var, primary_address, secondary_address):
    template = Template(json.dumps(template_var))
    return json.loads(template.render(primaryAddress=primary_address, secondaryAddress=secondary_address))


def render_slm_action(template, rule, rule_name, api):
    slm = getattr(rule, "slm", None)
    if slm:
        if not (None in list(rule.slm)):
            slm_action = deepcopy(template)
            slm_policy = api.slm.create("{rule_name}_SLM_policy".format(rule_name=rule_name), render_slm_statement(slm_statement_template ,rule.slm))
            slm_action["SLMPolicy"] = slm_policy["name"]
            return slm_action
    return None


def render_match_rules(template, primary_address, secondary_address, protocol):
    match_rule = deepcopy(template)
    if protocol == "http":
        match_rule["Url"] = "http://{ip}:{port}*".format(ip=primary_address, port=secondary_address)
    elif protocol == "mq":
        match_rule["Url"] = generate_mq_url_match(primary_address, secondary_address)

    return match_rule


def render_actions_list(template_var, filter_action, destination_action, slm_action=None):
    template = Template(json.dumps(template_var))
    rule_actions = json.loads(template.render(slm=slm_action, filter=filter_action, destination=destination_action))
    return [ast.literal_eval(str(action)) for action in rule_actions if action != "None"]


def __create_rule_handlers(primary_address, secondary_address, protocol, methods, rule_name, api, cluster_name, cluster_type):
    handlers = []
    if protocol == "http":
        handlers.append(api.http_handler.create("{rule_name}_HTTP_FSH".format(rule_name=rule_name), primary_address, secondary_address, "enabled", methods)["name"])
    elif protocol == "mq":
        envs = get_environments(cluster_name, cluster_type)
        if envs.get(primary_address):
            for i, qm in enumerate(envs[primary_address]):
                handler = api.mq_handler.create("{queue_name}_FSH_{id}".format(queue_name=secondary_address, id=(i+1)), qm, secondary_address, "enabled")
                handlers.append(handler["name"])
        else:
            handlers.append(api.mq_handler.create("{queue_name}_FSH".format(queue_name=secondary_address), primary_address, secondary_address, "enabled")["name"])
    return handlers


def render_error_rule(mpgw_name):
    error_rule = deepcopy(error_rule_template)
    error_rule["name"] = mpgw_name + "_error_rule"
    return error_rule


def populate_mpgw_template(req, api):
    mpgw = deepcopy(mpgw_template)
    req_obj = json2obj(json.dumps(req))
    details = req_obj.details
    mpgw["name"] = details.projectNameValue
    rules_names = []

    if validate_mpgw_name_is_free(api, mpgw["name"]) != False and validate_policy_handlers(api, req_obj.rules, details.clusterName, details.testOrProd):
        for rule in req_obj.rules:
            source, dest, rfilter = rule.srcAddr, rule.destAddr, rule.filter
            match, rule_obj = deepcopy(match_template), deepcopy(rule_template)
            rule_obj["name"] = "{mpgw}_{name}_rule".format(mpgw=mpgw["name"], name=rule.name)

            if not (rule_obj["name"] in rules_names):
                rules_names.append(rule_obj["name"])
                mpgw["handlers"] += __create_rule_handlers(source.primaryAddress, source.secondaryAddress, source.protocol, source.methods, rule_obj["name"], api, details.clusterName, details.testOrProd)
                slm_action = render_slm_action(slm_action_template, rule, rule_obj["name"], api)
                filter_action = render_filter_action(filters_templates, rfilter.dpasFilter, rfilter.schemaPath, rfilter.filterType, rfilter.schemaType)
                destination_action = render_destination_action(destination_templates[dest.protocol], dest.primaryAddress, dest.secondaryAddress)
                match["MatchRules"] = render_match_rules(match_rule_template, source.primaryAddress, source.secondaryAddress, source.protocol)
                rule_obj["match"] = match
                rule_obj["actions"] = render_actions_list(rule_actions_template, filter_action, destination_action, slm_action)
                mpgw["rules"].append(rule_obj)             

        mpgw["rules"].append(render_error_rule(mpgw["name"]))
        return mpgw
