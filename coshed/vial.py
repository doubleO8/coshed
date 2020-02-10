#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import datetime
import json
import time
from wsgiref.handlers import format_date_time
import pprint
from functools import wraps

import flask
from flask import render_template, request
try:
    from werkzeug.contrib.cache import SimpleCache
except ImportError:
    from cachelib import SimpleCache

import pendulum

import coshed

API_VERSION = os.environ.get("API_VERSION")

if API_VERSION is None:
    try:
        API_VERSION = coshed.__version__
    except Exception:
        API_VERSION = '0.0.42'

cache = SimpleCache()

NAVIGATION_ITEMS = [
    ('/', 'Home'),
    ('/doc', 'Documentation'),
]

WANT_DEV = ('i-like-my-sugar-with', 'coffee-and-cream')


def drop_dev(want_dev=None):
    if want_dev is None:
        want_dev = WANT_DEV

    try:
        (arg_name, expectation) = want_dev
        return not request.args.get(arg_name) == expectation
    except Exception:
        pass

    return True


def generate_expires_header(expires=False):
    """
    Generate HTTP expiration header.

    Args:
        expires: expiration in seconds or False for *imediately / no caching*

    Returns:
        dict: key/value pairs defining HTTP expiration information
    """
    headers = {}

    if expires is False:
        headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, ' \
                                   'post-check=0, pre-check=0, max-age=0'
        headers['Expires'] = '-1'
    else:
        now = datetime.datetime.now()
        expires_time = now + datetime.timedelta(seconds=expires)
        headers['Cache-Control'] = 'public'
        headers['Expires'] = format_date_time(
            time.mktime(expires_time.timetuple()))

    return headers


class AppResponse(dict):
    """
    Container class for chalice app responses.
    """

    def __init__(self, *args, **kwargs):
        self.drop_dev = kwargs.get("drop_dev")

        try:
            del kwargs['drop_dev']
        except Exception:
            pass

        dict.__init__(self, *args, **kwargs)

        if '_dev' not in self:
            self['_dev'] = dict()

        try:
            self['version'] = API_VERSION
        except NameError:
            self['version'] = '0.0.42'
        self['python_version'] = sys.version_info.major
        self['_now'] = pendulum.now(tz='UTC').strftime('%Y-%m-%d %H:%M:%S')

        if 'navigation' not in list(self.keys()):
            nav_items = list(self.navigation)
            if nav_items:
                self['navigation'] = nav_items

    @property
    def navigation(self):
        for data in NAVIGATION_ITEMS:
            try:
                (i_url, i_label, whitelist_key) = data
            except ValueError:
                whitelist_key = None
                (i_url, i_label) = data

            if whitelist_key and whitelist_key not in self.get("whitelist", []):
                continue
            yield i_url, i_label

    def flask_obj(self, status_code=200, drop_dev=None, with_version=True,
                  expires=None, headers=None, not_to_be_exposed=None):
        """
        Generate a :py:class:`flask.Response` object for current application
        response object.

        Args:
            status_code (int): HTTP status code, default 200
            drop_dev (bool): Drop development information
            with_version (bool): include version information
            expires: expiration specification
            headers (dict): headers
            not_to_be_exposed (iterable, optional): key/value pairs not to be exposed

        Returns:
            flask.Response: HTTP response object
        """
        del_keys = []

        if drop_dev is None:
            drop_dev = self.drop_dev

        if drop_dev:
            del_keys.append('_dev')

        if with_version is False:
            del_keys.append('version')

        if not_to_be_exposed:
            for ntbe in not_to_be_exposed:
                del_keys.append(ntbe)

        for del_key in del_keys:
            try:
                del self[del_key]
            except KeyError:
                pass

        if headers is None:
            headers = dict()

        headers["Content-Type"] = "application/json"

        if expires is not None:
            headers.update(generate_expires_header(expires))

        try:
            body = json.dumps(self, indent=2, sort_keys=True)
        except TypeError:
            body = pprint.pformat(self)
            headers["Content-Type"] = "text/plain"
            status_code = 500

        return flask.Response(
            status=status_code,
            headers=headers,
            response=body
        )


def request_wants_mimetype(mtb, other='text/html'):
    best = request.accept_mimetypes.best_match([mtb, other])
    return best == mtb and request.accept_mimetypes[best] > \
                           request.accept_mimetypes[other]


def request_wants_json():
    return request_wants_mimetype('application/json')


def cached(timeout=5 * 60, key='view/%s'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = key % request.path
            rv = cache.get(cache_key)
            if rv is not None:
                return rv
            rv = f(*args, **kwargs)
            cache.set(cache_key, rv, timeout=timeout)
            return rv

        return decorated_function

    return decorator


def cache_render_template(template_name, **context):
    expires_seconds = 60 * 60
    cache_key = template_name

    if context.get("expires"):
        expires_seconds = context.get("expires")
        del context["expires"]

    if context.get("cache_key"):
        cache_key = context.get("cache_key")
        del context["cache_key"]

    try:
        payload = cache.get(cache_key)
        if payload is None:
            raise KeyError(cache_key)
    except KeyError:
        payload = render_template(template_name, **context)
        cache.set(cache_key, payload, timeout=expires_seconds)

    # print payload, cache_key

    return payload


def format_version_tag(value):
    try:
        (base, _) = value.split('+', 1)
        return '{:s}*'.format(base)
    except ValueError:
        return value


def get_request_url(cf_port):
    """
    Hackfix: if we are on cloud foundry we always want HTTPS

    Returns:
        str: request URL
    """
    if cf_port is not None:
        return request.url.replace("http://", "https://")

    return request.url


JINJA_FILTERS = dict(
    # range_datetime=format_range_datetime,
    # on_off=format_on_off,
    # local_dt=format_local_dt,
    version_tag=format_version_tag,
)
