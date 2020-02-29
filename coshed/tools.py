#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json


def load_json(path):
    with open(path, "r") as src:
        content = json.load(src)

    return content


def next_best_specification_source(fallback, app_name=None, root_path=None):
    """
    Determine the best matching wolfication specification for *app_name*.

    Args:
        fallback: fallback source name
        app_name (unicode, optional): application name
        root_path (unicode, optional): path where specification files may be located

    Returns:
        unicode: specification path
    """
    candidates = list()

    if root_path is None:
        root_path = os.path.dirname(fallback)

    if app_name:
        candidates.append(
            os.path.join(
                root_path,
                'wolfication_specification.{app_name}.json'.format(
                    app_name=app_name)
            )
        )

    candidates.append(
        os.path.join(
            root_path,
            'wolfication_specification.json'
        )
    )

    for candy in candidates:
        if os.path.isfile(candy):
            return os.path.abspath(candy)

    return fallback
