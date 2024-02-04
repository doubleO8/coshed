#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import logging
import traceback
import json
import codecs

import pendulum


def log_traceback(message, exception, uselog=None):
    """
    Use *uselog* Logger to log a Traceback of exception *exception*.

    Args:
        message(str): message to be logged before trace log items
        exception(Exception): exception to be logged
        uselog(logging.Logger, optional): logger instance override

    """
    if uselog is None:
        uselog = logging.getLogger(__name__)
    e_type, e_value, e_traceback = sys.exc_info()

    uselog.warning(message)
    uselog.error(exception)

    for line in traceback.format_exception(e_type, e_value, e_traceback):
        for part in line.strip().split("\n"):
            if part != "":
                uselog.warning(part)


def dump_json(data, uselog=None, level=logging.INFO):
    """
    Log ``data`` in JSON format

    Args:
        data: data
        uselog(logging.Logger, optional): logger instance override
        level: logging level

    """
    if uselog is None:
        uselog = logging.getLogger(__name__)

    for line in json.dumps(data, indent=2).split("\n"):
        uselog.log(level, line)


def load_json(path):
    """
    Load JSON encoded file and return its contents.

    Args:
        path(str): path

    Returns:
        object: parsed content

    """
    with open(path, "r") as src:
        content = json.load(src)

    return content


def persist_json(data, path, indent=None, sort_keys=False):
    """
    Persist ``data`` in JSON format to ``path``.

    Args:
        data: data
        path: file path
        indent (int, optional): indent
        sort_keys (bool, optional): do sort keys

    """
    with codecs.open(path, "wb", "utf-8") as tgt:
        json.dump(data, tgt, indent=indent, sort_keys=sort_keys)


def next_best_specification_source(
    fallback, app_name=None, root_path=None, trunk=None
):
    """
    Determine the best matching wolfication specification for *app_name*.

    Args:
        fallback: fallback source name
        app_name (unicode, optional): application name
        root_path (unicode, optional): path where specification files may be located
        trunk (unicode, optional): specification file trunk

    Returns:
        unicode: specification path
    """
    candidates = list()

    if root_path is None:
        root_path = os.path.dirname(fallback)

    if trunk is None:
        trunk = "wolfication_specification"

    if app_name:
        candidates.append(
            os.path.join(
                root_path,
                "{trunk}.{app_name}.json".format(
                    app_name=app_name, trunk=trunk
                ),
            )
        )

    candidates.append(
        os.path.join(root_path, "{trunk}.json".format(trunk=trunk))
    )

    for candy in candidates:
        if os.path.isfile(candy):
            return os.path.abspath(candy)

    return fallback


def next_best_asset_source(fallback, app_name=None, root_path=None):
    """
    Determine the best matching wolfication index for *app_name*.

    Args:
        fallback: fallback source name
        app_name (unicode, optional): application name
        root_path (unicode, optional): path where specification files may be located

    Returns:
        unicode: index path
    """
    return next_best_specification_source(
        fallback, app_name=app_name, root_path=root_path, trunk="index"
    )


def period_object(period):
    """
    Convert *period* to  a ``pendulum.Period`` object if needed and possible.

    Args:
        period: input data

    Returns:
        period (pendulum.Period): period object
    """
    if isinstance(period, dict):
        try:
            try:
                return pendulum.Period(
                    pendulum.parse(period["begin"]),
                    pendulum.parse(period["end"]),
                )
            except KeyError:
                return pendulum.Period(
                    pendulum.parse(period["start"]),  # allowing also 'start'
                    pendulum.parse(period["end"]),
                )
        except KeyError:
            raise ValueError(
                "Cannot make a period object out of {!r}".format(period)
            )
    elif isinstance(period, pendulum.Period):
        return period

    raise ValueError("Cannot make a period object out of {!r}".format(period))


def period_json(period):
    """
    Convert a ``pendulum.Period`` object to a JSON serialisable dict.

    Args:
        period (pendulum.Period): period object

    Returns:
        dict: period specification
    """
    if isinstance(period, dict):
        period = period_object(period)

    return {
        "total_seconds": period.total_seconds(),
        "begin": period.start.to_iso8601_string(),
        "end": period.end.to_iso8601_string(),
    }
