from flask_inputs import Inputs
from flask_inputs.validators import JsonSchema


mq_handler_schema = {
    "anyOf": [
        {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "queue_manager": {
                        "type": "string"
                    },
                    "get_queue": {
                        "type": "string"
                    },
                    "state": {
                        "type": "string"
                    }
                },
                "required": [
                    "name",
                    "queue_manager",
                    "get_queue",
                    "state"
                ]
            }
        },
        {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "queue_manager": {
                    "type": "string"
                },
                "get_queue": {
                    "type": "string"
                },
                "state": {
                    "type": "string"
                }
            },
            "required": [
                "name",
                "queue_manager",
                "get_queue",
                "state"
            ]
        }
    ]
}

http_handler_schema = {
    "anyOf": [
        {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "local_address": {
                        "type": "string",
                        "format": "ipv4"
                    },
                    "local_port": {
                        "type": "string",
                        "pattern": "\d{4}"
                    },
                    "state": {
                        "type": "string"
                    },
                    "allowed_features": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "examples": [
                                "GET",
                                "POST",
                                "PUT"
                            ]
                        }
                    }
                },
                "required": [
                    "name",
                    "local_address",
                    "local_port",
                    "state",
                    "allowed_features",
                ]
            }
        },
        {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "local_address": {
                    "type": "string"
                },
                "local_port": {
                    "type": "string",
                    "pattern": "^\d{4}$"
                },
                "state": {
                    "type": "string"
                },
                "allowed_features": {
                    "type": "array",
                    "items": {
                            "type": "string",
                            "examples": [
                                "GET",
                                "POST",
                                "PUT"
                            ]
                    }
                }
            },
            "required": [
                "name",
                "local_address",
                "local_port",
                "state",
                "allowed_features",
            ]
        }
    ]
}


class MQHandlerInputs(Inputs):
    json = [JsonSchema(schema=mq_handler_schema)]


class HTTPHandlerInputs(Inputs):
    json = [JsonSchema(schema=http_handler_schema)]


def validate_mq_handler(request):
    inputs = MQHandlerInputs(request)
    if inputs.validate():
        return None
    else:
        return inputs.errors


def validate_http_handler(request):
    inputs = HTTPHandlerInputs(request)
    if inputs.validate():
        return None
    else:
        return inputs.errors
