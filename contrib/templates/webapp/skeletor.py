#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web app skeleton
"""
from __future__ import absolute_import
from builtins import range

import os
import logging

from flask import Flask, abort, render_template, request
from flask import send_from_directory, url_for
import pendulum

from coshed.vial import JINJA_FILTERS
from coshed.tools import load_json
from coshed.flask_tools import wolfication
from coshed.vial import AppResponse

STATIC = '{{ static_folder }}'

BRAND_NAME = '{{ brand_name }}'

APP_NAME = '{{ app_name }}'

ASSETS_JSON = '{{ index_file | default("index.json")}}'

DEBUG_FLAG = True

#: logger instance
LOG = logging.getLogger(APP_NAME)

#: flask application instance
app = wolfication(
    Flask(__name__, static_folder=STATIC),
    jinja_filters=JINJA_FILTERS, app_name=APP_NAME)

assets = load_json(os.path.join(STATIC, ASSETS_JSON))


@app.route('/favicon.ico')
def favicon_handler():
    return send_from_directory(STATIC, 'favicon.ico')


@app.route('/')
def root_handler():
    data = AppResponse(
        assets=assets,
        title="skeletor",
        brand_name=BRAND_NAME,
    )

    return data.flask_obj()


if __name__ == '__main__':
    port = int('{{ listen_port }}')
    bind_address = '0.0.0.0'

    app.run(host=bind_address, port=port, debug=DEBUG_FLAG)
