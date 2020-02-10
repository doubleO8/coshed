#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from future import standard_library

standard_library.install_aliases()
import os
import hashlib
import io as StringIO
import json
import codecs
import platform
import subprocess
import argparse
import logging
import re

import six
from coshed.tools import load_json

PATTERN_VALID_APP_NAME = r'[a-z]+[a-z0-9\-\_]*[a-z0-9]+'
REGEX_VALID_APP_NAME = re.compile(PATTERN_VALID_APP_NAME, re.I)

LOG = logging.getLogger(__name__)


def combine(sources, root_path, trunk=None):
    included_sources = 0
    if isinstance(sources, six.string_types):
        sources = [sources]

    sources = [os.path.abspath(os.path.join(root_path, x)) for x in sources]
    folder = os.path.dirname(sources[0])
    b_name0 = os.path.basename(sources[0])
    trunk0, ext = os.path.splitext(b_name0)

    if trunk is None:
        trunk = trunk0

    LOG.info("Combining ...")
    LOG.debug(" folder: {!s}".format(folder))
    LOG.debug(" trunk : {!s}{!s}".format(trunk0, ext))

    content = StringIO.StringIO()
    hash_cookie = hashlib.sha1()
    source_end = "\n"

    for source in sources:
        if not os.path.exists(source):
            LOG.error("Source missing: {!s}".format(source))
            continue
        LOG.debug("  + {!s}".format(source))
        included_sources += 1

        with codecs.open(source, "rb", 'utf-8') as src:
            chunk = src.read(1024).replace('sourceMappingURL', '')
            while chunk:
                content.write(chunk)
                hash_cookie.update(chunk.encode('utf-8'))
                chunk = src.read(1024).replace('sourceMappingURL', '')

        try:
            content.write(source_end)
        except TypeError:
            content.write(unicode(source_end))
        hash_cookie.update(source_end.encode('utf-8'))

    filename = '{trunk}-{hexdigest}{ext}'.format(
        trunk=trunk, hexdigest=hash_cookie.hexdigest(), ext=ext)
    target = os.path.join(folder, filename)
    content.seek(0)

    if included_sources:
        LOG.info(" ... {!s}".format(target))

        with codecs.open(target, "wb", 'utf-8') as tgt:
            tgt.write(content.read())
    else:
        LOG.info(" ... NO CONTENT.")
        raise ValueError("No content")

    return os.path.relpath(target, root_path).replace("\\", '/')


def remove_old_combined(index_path, root_path):
    with codecs.open(index_path, "rb", 'utf-8') as src:
        source_specification = json.load(src)

    delete_me = list()

    for root in source_specification:
        for item_key in source_specification[root]:
            items = source_specification[root][item_key]

            if isinstance(items, six.string_types):
                items = [items]

            delete_me += items

    for item_rel in delete_me:
        item = os.path.abspath(os.path.join(root_path, item_rel))
        # print(item)
        if not os.path.isfile(item):
            continue

        os.unlink(item)


def export_index(index_path, assets):
    with codecs.open(index_path, "wb", 'utf-8') as tgt:
        json.dump(assets, tgt, indent=2, sort_keys=True)


def bundle(source_specification, index_path=None, app_name=None):
    assets = dict()
    root_path = source_specification['_static']

    if index_path is None:
        index_path = os.path.join(root_path, "index.json")

        if app_name:
            index_path = os.path.join(
                root_path, "index.{:s}.json".format(app_name))

    LOG.info("'static files' root path: {!s}".format(
        source_specification['_static']))
    LOG.info("index path: {!s}".format(index_path))

    if os.path.isfile(index_path):
        remove_old_combined(index_path, root_path=root_path)

    for root in source_specification:
        asset_items = dict()

        if root.startswith('_'):
            continue

        for item_key in source_specification[root]:
            trunk = item_key
            items = source_specification[root][item_key]

            if app_name:
                trunk = '.'.join((item_key, app_name))

            try:
                items_combined = combine(items,
                                         trunk=trunk, root_path=root_path)
            except ValueError as vexc:
                LOG.warning(vexc)
                continue

            asset_items[item_key] = [items_combined]

        assets[root] = asset_items

    export_index(index_path, assets)

    return assets


def cli_stub(**kwargs):
    app_name = None
    description = "Web application bundling"
    defaults = dict(
        source_path=os.path.join(
            os.getcwd(), 'static/wolfication_specification.json'
        ),
        uwsgi_config_path=os.path.join(os.getcwd(), 'contrib/uwsgi-emperor/')
    )

    for kw_key in ("source_path", "uwsgi_config_path", "index_path"):
        val = kwargs.get(kw_key)
        if val is not None:
            defaults[kw_key] = val

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('app_name', metavar='APP',
                        help='web application name', nargs='?')

    # parser.add_argument(
    #     '-n', '--dry-run', action='store_true',
    #     dest="dry_run",
    #     default=False, help="Dry run mode")

    # parser.add_argument(
    #     '-f', '--force', action='store_true',
    #     dest="force",
    #     default=False, help="force mode (overwrites stuff etc.)")

    parser.add_argument(
        '-s', '--specification-source', default=defaults['source_path'],
        help="Sources specification. Default: %(default)s", dest="source_path",
        metavar="PATH"
    )

    parser.add_argument(
        '-i', '--assets-index', default=None,
        help="Assets index path", dest="index_path",
        metavar="PATH"
    )

    parser.add_argument(
        '-u', '--uwsgi-configuration-path',
        default=defaults['uwsgi_config_path'],
        help="uWSGI configuration path. Default: %(default)s",
        dest="uwsgi_config_path", metavar="PATH"
    )

    cli_args = parser.parse_args()

    source_specification = load_json(cli_args.source_path)
    try:
        source_specification['_static']
    except KeyError:
        source_specification['_static'] = os.path.dirname(cli_args.source_path)

    if cli_args.app_name:
        if re.match(REGEX_VALID_APP_NAME, cli_args.app_name):
            app_name = cli_args.app_name
        else:
            LOG.warning("Invalid app name {!r}, "
                        "valid names regular expression is {!s}".format(
                cli_args.app_name, PATTERN_VALID_APP_NAME))
            raise ValueError("Invalid app name")

    bundle(source_specification,
           index_path=cli_args.index_path, app_name=app_name)

    if os.path.isdir(cli_args.uwsgi_config_path):
        uwsgi_files = list()

        for item in os.listdir(cli_args.uwsgi_config_path):
            uwsgi_files.append(item)

        if platform.system() != 'Linux':
            LOG.warning("Crippled platform, skipping uWSGI magic")
        else:
            for uw_file in uwsgi_files:
                args = [
                    'touch',
                    os.path.abspath(
                        os.path.join(cli_args.uwsgi_config_path, uw_file))
                ]
                subprocess.call(args)
