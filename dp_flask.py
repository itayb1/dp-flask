#!/usr/bin/env python3

from flask import Flask
from flask_cors import CORS
from views import mpgw_api, http_handler_api, mq_handler_api, status_api, misc_api, lbg_api, template_api

app = Flask(__name__)
CORS(app)

app.register_blueprint(mpgw_api)
app.register_blueprint(mq_handler_api)
app.register_blueprint(http_handler_api)
app.register_blueprint(status_api)
app.register_blueprint(misc_api)
app.register_blueprint(lbg_api)
app.register_blueprint(template_api)


@app.route("/", methods=['GET', 'POST'])
def hello():
    return "Hi"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)
