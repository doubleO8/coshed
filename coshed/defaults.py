#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

COSH_FILE_DEFAULT = 'cosh.json'

PROJECT_ROOT = os.getcwd()

SCSS_ROOT = os.path.join(PROJECT_ROOT, 'scss')
JS_ROOT = os.path.join(PROJECT_ROOT, 'js')
SCRIPTS_D_ROOT = os.path.join(PROJECT_ROOT, 'contrib/cosh_scripts.d')

#: css-html-js-minify script path
CSS_HTML_JS_MINIFY_BINARY = "css-html-js-minify.py"

#: closure-compiler path
CLOSURE_COMPILER_BINARY = "closure-compiler"

#: default environment key to configuration key mappings
ENV_MAP = [
    ("COSH_SCSS", "scss"),
    ("COSH_INOTIFYWAIT", 'inotifywait'),
    ("COSH_CSS_HTML_JS_MINIFY", CSS_HTML_JS_MINIFY_BINARY),
    ("COSH_CLOSURE_COMPILER", CLOSURE_COMPILER_BINARY),
]

#: default configuration values
COSHED_CONFIG_DEFAULTS = dict(
    #: default scss arguments
    scss_args=[
        "-t compressed",
        "--unix-newlines",
        "--sourcemap=none"
    ],
    #: default inotifywait arguments
    inotifywait_args=[
        "-r",
        "-e modify"
    ],
    #: root path being watched by inotifywait
    watched_root=SCSS_ROOT,
    #: list of tuples: source (SCSS) -> target (CSS) locations
    scss_map=[
        # ('x.scss', 'y.css'),
    ],
    #: list of paths: Javascript files to concatenate
    concat_js_sources=[],
    concat_js_trunk=os.path.join(JS_ROOT, 'lib.bundle.js'),
    concat_js_compiler="closure",
    #: default locations of used binaries
    inotifywait="inotifywait",
    scss="scss",
    #: functions to be called when a change in *watched_root* is detected
    onchange=["call_scss", 'call_js', 'call_scripts'],
    #: path where scripts are located which shall be called on changes to
    #: *watched_root*
    scripts_d=SCRIPTS_D_ROOT,
    css_html_js_minify=CSS_HTML_JS_MINIFY_BINARY,
    closure_compiler=CLOSURE_COMPILER_BINARY,
    #: keys for which relative paths to *coshfile* are enforced
    cosh_force_relative_paths=[
        "watched_root",
        "scripts_d",
        "concat_js_sources",
        "concat_js_trunk",
        "scss_map"
    ],
    rsync_source="",
    rsync_destination="",
    rsync_exclude_from="",
    rsync_args=[
        "-avrn"
    ]
)
