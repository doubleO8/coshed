#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import logging
import argparse

import coshed
from coshed.coshed_config import CoshedConfig, COSH_FILE_DEFAULT
from coshed.coshed_watcher import CoshedWatcher

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

LOG = logging.getLogger("coshed_watcher")

PROJECT_ROOT = os.getcwd()

SCSS_ROOT = os.path.join(PROJECT_ROOT, 'scss')
JS_ROOT = os.path.join(PROJECT_ROOT, 'js')
SCRIPTS_D_ROOT = os.path.join(PROJECT_ROOT, 'contrib/cosh_scripts.d')

#: default environment key to configuration key mappings
ENV_MAP = [
    ("COSH_SCSS", "scss"),
    ("COSH_INOTIFYWAIT", 'inotifywait'),
]

#: default configuration values
DEFAULTS = dict(
    #: default scss arguments
    scss_args=[
        "-t compressed",
        "--unix-newlines",
        "--sourcemap=none"
    ],
    #: default inotifywait arguments
    inotifywait_args=[
        "-r", "-e modify"
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
    #: default locations of used binaries
    inotifywait="inotifywait",
    scss="scss",
    #: functions to be called when a change in *watched_root* is detected
    onchange=["call_scss", 'call_js', 'call_scripts'],
    #: path where scripts are located which shall be called on changes to
    #: *watched_root*
    scripts_d=SCRIPTS_D_ROOT
)

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(epilog="coshed {:s}".format(
        coshed.__version__))
    argparser.add_argument(
        '--cosh-file', '-f',
        dest="coshfile", default=COSH_FILE_DEFAULT, metavar="PATH",
        help="JSON config file [%(default)s]")
    argparser.add_argument(
        '--force-update', '-u', action='store_true',
        dest="force_update",
        help="Force updating of CSS files and terminate", default=False)
    argparser.add_argument(
        '--verbose', '-v', action='count',
        default=0, dest="verbose",
        help="verbosity (more v: more verbosity)")

    args = argparser.parse_args()

    cosh_cfg = CoshedConfig(
        defaults=DEFAULTS,
        coshfile=args.coshfile,
        environ_key_mapping=ENV_MAP,
    )

    LOG.warning("inotifywait and scss binaries need to be installed!")
    LOG.warning(
        " 'apt-get install inotify-tools ruby-sass' on debian "
        "derived distributions")
    LOG.waring("For JavaScript minification css-html-js-minify"
               "needs to be installed.")
    for env_key, key in ENV_MAP:
        LOG.debug(
            "You may use environment variable {env_key!r} to "
            "override configuration key {key!r}.".format(
                env_key=env_key, key=key))

    if args.verbose > 0:
        LOG.debug("Supported S/CSS transformations:")
        for (src, dst) in cosh_cfg.scss_map:
            LOG.debug("{!r} -> {!r}".format(src, dst))

    if args.verbose > 1:
        LOG.info("coshed configuration:")
        LOG.info(cosh_cfg)

    cosh_op = CoshedWatcher(cosh_cfg)

    if args.force_update:
        cosh_op.on_change()
        sys.exit(0)

    try:
        cosh_op.watch()
    except KeyboardInterrupt:
        LOG.info("\nAborted.")
