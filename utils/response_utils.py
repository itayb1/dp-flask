from flask import jsonify

def success_response(msg):
    message = {
        'status': 200,
        'message': msg
    }
    resp = jsonify(message)
    resp.status_code = 200
    return resp


def handle_error(error):
    message = {
            'status': error.status_code,
            'message': error.message
    }
    resp = jsonify(message)
    resp.status_code = error.status_code
    return resp
