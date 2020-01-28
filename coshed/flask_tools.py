#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid
import logging
from logging.handlers import RotatingFileHandler

from flask import abort, jsonify
from flask_cors import CORS
from flask_compress import Compress
import six
import six.moves.urllib.parse as urlparse

from coshed.swagger_glue import next_best_swagger_in_source
from coshed.tools import load_json

#: custom log formatter
formatter = logging.Formatter(
    fmt='%(asctime)s %(name)-16s %(levelname)-8s %(funcName)-15s '
        '(#%(lineno)04d): %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')


def rotating_app_log(flask_app_instance, app_name=None):
    if app_name is None:
        app_name = uuid.uuid4().hex

    log_filename = '/tmp/{:s}-webapp.log'.format(app_name)
    handler = RotatingFileHandler(log_filename, maxBytes=10000, backupCount=1)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    flask_app_instance.logger.addHandler(handler)
    flask_app_instance.logger.setLevel(logging.INFO)
    logging.getLogger("iotta.boarding_queue").addHandler(handler)

    return log_filename


def wolfication(flask_app_instance=None, jinja_filters=None, app_name=None):
    flask_app_instance.jinja_env.trim_blocks = True
    flask_app_instance.jinja_env.lstrip_blocks = True
    flask_app_instance.jinja_env.strip_trailing_newlines = True
    flask_app_instance.config['SEND_FILE_MAX_AGE_DEFAULT'] = 24 * 3600 * 365
    flask_app_instance.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

    if jinja_filters is not None:
        for (filter_key, filter_func) in six.iteritems(jinja_filters):
            flask_app_instance.jinja_env.filters[filter_key] = filter_func

    CORS(flask_app_instance)
    Compress(flask_app_instance)

    if app_name is not None:
        rotating_app_log(flask_app_instance, app_name)

    return flask_app_instance


def serve_swagger_handler(swagger_root_path, app_name=None, overrides=None):
    """
    Load swagger specification, apply overrides and return Flask HTTP
    response object.

    Args:
        swagger_root_path: swagger files path
        app_name: application name
        overrides (dict): specification overrides

    Returns:
        Flask.Response: HTTP response object
    """
    try:
        swagger_in = next_best_swagger_in_source(swagger_root_path,
                                                 app_name=app_name)
    except ValueError:
        abort(404)

    swagger_content = load_json(swagger_in)
    if overrides is not None:
        swagger_content.update(overrides)

    return jsonify(swagger_content)
