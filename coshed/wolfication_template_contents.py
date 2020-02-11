#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

site_conf = """
server {
    access_log /var/log/nginx/{{ app_name }}-access.log combined;
    error_log  /var/log/nginx/{{ app_name }}-error.log info;

    set $app_root {{ app_root }};
    set $static {{ static_folder|default('$app_root/static') }};

    listen      {{ listen_port }};

    root $static;

    charset     utf-8;
    client_max_body_size 12M;
    client_body_buffer_size 2M;

    # serve static files
    location /static {
        alias $static;
        include snippets/enable_cors;
        access_log off;

        expires +14d;
        add_header Cache-Control public;
    }

    location / {
        include snippets/enable_cors;
        include uwsgi_params;
        uwsgi_pass unix:/opt/uwsgi-sockets/{{ app_name }};
    }

    # Enable gzip but do not remove ETag headers
    gzip on;
    gzip_vary on;
    gzip_comp_level 4;
    gzip_min_length 256;
    gzip_proxied expired no-cache no-store private no_last_modified no_etag auth;
    gzip_types application/javascript application/json text/javascript text/css text/html;
}
"""

app_ini = """
[uwsgi]
processes = 2
uid = www-data

#application's base folder
base = {{ app_root }}
chdir = %(base)

# python module to import
module = {{ app_name }}

# flask instance
callable = app

virtualenv = %(base)/venv

socket = /opt/uwsgi-sockets/%n
chmod-socket    = 666

logto = /var/log/uwsgi/vassals/%n.log
plugins = {{ uwsgi_plugin|default('python3') }}
"""

skeletor_py = '''
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
'''

requirements_txt = """
requests>=2.13.0
pendulum==2.0.5
future==0.18.2
six==1.13.0
Jinja2==2.10.3
Flask==1.1.1
Flask-Compress==1.4.0
Flask-Cors==3.0.7
coshed>=0.5.0
cachelib==0.1
"""

gitignore = """
.DS_Store
._*
*.py[cod]
/.idea
*~
.sass-cache/
*.css.map
/cosh.json
/dist
/MANIFEST
/scss
/js
/venv
/venv3
/*.egg-info
"""

cfignore = """
/contrib
"""

spec_empty = {
    "css": {
        "lib": [
            "css/lib_dummy.css"
        ],
        "app": [
            "css/app_dummy.css"
        ]
    },
    "js": {
        "lib": [
            "js/lib_dummy.js",
        ],
        "app": [
            "js/app_dummy.js"
        ]
    }
}

wolfication_specification = json.dumps(spec_empty, indent=2, sort_keys=True)

TEMPLATES_CONTENT = {
    '{templates_root}/nginx/site.conf.jinja2': site_conf,
    '{templates_root}/uwsgi-emperor/app.ini.jinja2': app_ini,
    '{templates_root}/skeletor.py': skeletor_py,
    '{project_root}/requirements.txt': requirements_txt,
    '{project_root}/.gitignore': gitignore,
    '{project_root}/.cfignore': cfignore,
    '{static_folder}/wolfication_specification.{app_name}.json': wolfication_specification,
}
