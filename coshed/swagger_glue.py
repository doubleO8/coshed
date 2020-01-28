#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os


def next_best_swagger_in_source(swagger_root_path, app_name=None):
    """
    Determine the best matching swagger specification for *app_name*.

    Args:
        swagger_root_path: swagger files path
        app_name: application name

    Returns:
        unicode: swagger specification path

    Raises:
        ValueError: in case no swagger specification file could be found
    """
    swagger_in_candidates = list()

    if app_name:
        swagger_in_candidates.append(
            'swagger.{app_name}.in.json'.format(app_name=app_name))

    swagger_in_candidates.append('swagger.in.json')

    for candy in swagger_in_candidates:
        candy_path = os.path.join(swagger_root_path, candy)
        if os.path.isfile(candy_path):
            return os.path.abspath(candy_path)

    raise ValueError("No swagger.in file found")
