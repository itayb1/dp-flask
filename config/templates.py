rule_actions_template = [
    "{{ slm }}",
    {
        "Type": "gatewayscript",
        "Input": "INPUT",
        "Output": "dpvar1",
        "GatewayScriptLocation": "local:///NonXMlReader.js"
    },
    "{{ filter  }}",
    "{{ destination }}",
    {
        "Type": "xform",
        "Input": "NULL",
        "Output": "NULL",
        "Transform": "local:///JsonLOG.xsl"
    },
    {
        "Type": "results",
        "Input": "INPUT",
        "Output": "NULL"
    }
]


slm_statement_template = {
    "action": "{{ action }}",
    "interval": "{{ interval|int }}",
    "intervalType": "{{ intervalType }}",
    "thresholdAlgorithm": "{{ thresholdAlgorithm }}",
    "thresholdType": "{{ thresholdType }}",
    "thresholdLevel": "{{ thresholdLevel|int }}"
}


slm_action_template = {
    "Type": "slm",
    "Input": "INPUT",
    "SLMPolicy": "SLM_Test_Policy",
}


destination_templates = {
    "http": {
        "Type": "xform",
        "Input": "NULL",
        "Output": "NULL",
        "Transform": "local:///RouteUriV2.xsl",
        "StylesheetParameters": [
                {
                    "ParameterName": "Destination",
                    "ParameterValue": "http://{{ primaryAddress }}:{{ secondaryAddress }}*"
                }
        ]
    },
    "mq": {
        "Type": "xform",
        "Input": "NULL",
        "Output": "NULL",
        "Transform": "local:///MultiRoute.xsl",
        "StylesheetParameters": [
            {
                "ParameterName": "Environment",
                "ParameterValue": "{{ primaryAddress }}"
            },
            {
                "ParameterName": "Queue",
                "ParameterValue": "{{ secondaryAddress }}"
            },

        ]
    }
}


filters_templates = {
    "schema":
        {
            "Type": "validate",
            "Input": "dpvar1",
            "Output": "NULL",
            "SchemaURL": "local:///testSchhema.xsd"
        },
    "dpas":
        {
            "Type": "validate",
            "Input": "dpvar1",
            "Output": "NULL",
            "SchemaURL": "local:///testSchhema.xsd"
        },
    "green": None

}


match_rule_template = {
    "Type": "fullyqualifiedurl",
    "HttpTag": "",
    "HttpValue": "",
    "Url": "",
    "ErrorCode": "",
    "XPATHExpression": "",
    "Method": "default",
    "CustomMethod": ""
}


match_template = {
    "MatchRules": [

    ],
    "MatchWithPCRE": "on",
    "CombineWithOr": "on"
}


rule_template = {
    "name": "",
    "direction": "request-rule",
    "actions": "",
    "match": ""
}


mpgw_template = {
    "name": "Test_MP",
    "rules": [],
    "handlers": []
}


error_rule_template = {
    "name": "Test_MP_error_rule",
    "direction": "error-rule",
    "actions": [
        {
            "Type": "xform",
            "Input": "NULL",
            "Output": "NULL",
            "Transform": "local:///WhenNetworkError.xsl"
        },
        {
            "Type": "results",
            "Input": "INPUT",
            "Output": "NULL"
        }
    ],
    "match": {
        "MatchRules": [
            {
                "Type": "fullyqualifiedurl",
                "HttpTag": "",
                "HttpValue": "",
                "Url": "*",
                "ErrorCode": "",
                "XPATHExpression": "",
                "Method": "PUT",
                "CustomMethod": ""
            }
        ],
        "MatchWithPCRE": "off",
        "CombineWithOr": "off"
    }
}