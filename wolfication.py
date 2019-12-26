#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from builtins import object
import os
import sys
import random
import logging
import argparse
import copy
import codecs

from jinja2 import Environment, FileSystemLoader

from coshed import bundy

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

CONTRIB = os.path.abspath(
    os.path.join(PROJECT_ROOT, 'contrib')
)

sys.path.insert(0, PROJECT_ROOT)

TEMPLATES = os.path.abspath(
    os.path.join(CONTRIB, 'templates/webapp')
)

env = Environment(loader=FileSystemLoader(TEMPLATES))

TEMPLATE_ARGS = dict(
    app_root=os.path.abspath(os.getcwd()),
    brand_name=None,
)

TEMPLATE_ARGS['static_folder'] = os.path.join(
    TEMPLATE_ARGS['app_root'], 'static')

CONFIGURATION_FOLDERS = dict(
    uwsgi_vassals='/etc/uwsgi-emperor/vassals',
    nginx_sites_available='/etc/nginx/sites-available',
    nginx_sites_enabled='/etc/nginx/sites-enabled',
)

CONFIGURATION_FOLDERS_CENTOS = dict(
    uwsgi_vassals='/etc/uwsgi.d',
    nginx_conf_d='/etc/nginx/conf.d',
)


class Wolfication(object):
    def __init__(self, app_name, listen_port=None, *args, **kwargs):
        self.log = logging.getLogger(__name__)
        self.dry_run = kwargs.get("dry_run", False)

        if listen_port is None:
            listen_port = random.randint(23000, 60000)
        else:
            listen_port = int(listen_port)

        self.template_args = {
            "app_name": app_name,
            "listen_port": listen_port,
        }
        self.template_args.update(TEMPLATE_ARGS)

        for key in kwargs:
            self.template_args[key] = kwargs[key]

        if self.template_args['brand_name'] is None:
            self.template_args['brand_name'] = app_name

    def skeleton_app(self):
        template = env.get_template('skeletor.py')
        return template.render(**self.template_args)

    def nginx_site(self):
        template = env.get_template('nginx/site.conf.jinja2')
        return template.render(**self.template_args)

    def uwsgi_vassal(self):
        template = env.get_template('uwsgi-emperor/app.ini.jinja2')
        return template.render(**self.template_args)

    def _dump(self, path, content, overwrite=False):
        if os.path.exists(path) and not overwrite:
            raise IOError("existis: {!s}".format(path))

        with codecs.open(path, "wb", 'utf-8') as tgt:
            tgt.write(content)

    def instructor(self, spec, configuration_folders=None):
        if configuration_folders is None:
            configuration_folders = CONFIGURATION_FOLDERS

        merged = copy.copy(configuration_folders)

        for key in spec:
            merged[key] = spec[key][0]

        merged['nginx_config_bname'] = os.path.basename(merged['nginx_config'])

        messages = [
            '#' * 80,
            '# Installation instructions ...',
            '#' * 80,
            'ln -s {uwsgi_config} {uwsgi_vassals}'.format(**merged),
        ]

        if 'nginx_sites_available' in merged:
            messages.append(
                'ln -s {nginx_config} {nginx_sites_available}'.format(
                    **merged))
            messages.append(
                'ln -s '
                '{nginx_sites_available}/{nginx_config_bname} '
                '{nginx_sites_enabled}'.format(**merged))
        else:
            messages.append(
                'ln -s {nginx_config} {nginx_conf_d}'.format(**merged))

        for msg in messages:
            self.log.info(msg)

    def persist(self):
        spec = dict(
            nginx_config=('{contrib}/nginx/{app_name}.conf'.format(
                contrib=CONTRIB, **self.template_args), self.nginx_site),
            uwsgi_config=('{contrib}/uwsgi-emperor/{app_name}.ini'.format(
                contrib=CONTRIB, **self.template_args), self.uwsgi_vassal),
            app=('{project_root}/{app_name}.py'.format(
                project_root=PROJECT_ROOT, **self.template_args),
                 self.skeleton_app),
        )

        self.log.info(
            "Creating {app_name} on port {listen_port} with "
            "app_root {app_root}".format(**self.template_args))

        if self.dry_run:
            self.log.info("DRY RUN.")

        for target, func in list(spec.values()):
            if self.dry_run:
                self.log.info("WOULD write {!s}".format(target))
                continue

            self.log.debug(target)
            target_parent = os.path.dirname(target)
            if not os.path.isdir(target_parent):
                os.makedirs(target_parent)
            self._dump(target, func(), overwrite=self.template_args['force'])
        self.instructor(spec, self.template_args['configuration_folders'])

        source_path = os.path.join(
            self.template_args['static_folder'],
            'wolfication_specification.json'
        )

        if os.path.isfile(source_path):
            bundy.cli_stub(source_path)


if __name__ == '__main__':
    description = "Webapp skeleton generator"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('app_name', metavar='APP',
                        help='web application name')

    parser.add_argument(
        '-n', '--dry-run', action='store_true',
        dest="dry_run",
        default=False, help="Dry run mode")

    parser.add_argument(
        '-f', '--force', action='store_true',
        dest="force",
        default=False, help="force mode (overwrites stuff etc.)")

    parser.add_argument(
        '-p', '--port', default=None, type=int,
        help="listening port", dest="listen_port"
    )

    parser.add_argument(
        '--platform-centos', default=CONFIGURATION_FOLDERS,
        action="store_const",
        const=CONFIGURATION_FOLDERS_CENTOS,
        help="Use CentOS platform configuration defaults",
        dest="configuration_folders"
    )

    params_group = parser.add_argument_group("More Parameters")
    for key in TEMPLATE_ARGS:
        params_group.add_argument(
            '--{:s}'.format(key), default=TEMPLATE_ARGS[key],
            help="{:s}. Default is %(default)s".format(key),
            dest=key
        )

    cli_args = parser.parse_args()
    wolfication = Wolfication(**vars(cli_args))
    wolfication.persist()
