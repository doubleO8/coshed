#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import logging
import argparse
import glob

import coshed
from coshed.coshed_config import CoshedConfig, COSH_FILE_DEFAULT

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

LOG = logging.getLogger("coshed_watcher")

PROJECT_ROOT = os.getcwd()

SCSS_ROOT = os.path.join(PROJECT_ROOT, 'scss')
SCRIPTS_D_ROOT = os.path.join(PROJECT_ROOT, 'contrib/cosh_scripts.d')

ENV_MAP = [
    ("COSH_SCSS", "scss"),
    ("COSH_INOTIFYWAIT", 'inotifywait'),
]

DEFAULTS = dict(
    #: default scss arguments
    scss_args=[
        "-t compressed",
        "--unix-newlines",
        "--sourcemap=none"
    ],
    inotifywait_args=[
        "-r", "-e modify"
    ],
    # root path being watched by inotifywait
    watched_root=SCSS_ROOT,
    #: source (SCSS) -> target (CSS) locations
    scss_map=[
    ],
    #: default locations of used binaries
    inotifywait="inotifywait",
    scss="scss",
    #: functions to be called when a change in *watched_root* is detected
    onchange=["call_scss", 'call_scripts'],
    scripts_d=SCRIPTS_D_ROOT
)


def call_scss(cosh_config_obj):
    if not cosh_config_obj.scss_map:
        LOG.debug("Empty scss_map!")

    for (src, dst) in cosh_config_obj.scss_map:
        scss_call = '{binary} {args} "{src}":"{dst}"'.format(
            binary=cosh_config_obj.scss,
            args=' '.join(cosh_config_obj.scss_args),
            src=src, dst=dst)
        LOG.info(" {!s}".format(scss_call))
        scss_rc = subprocess.call(scss_call, shell=True)
        LOG.info("# RC={!s}".format(scss_rc))


def call_scripts(cosh_config_obj):
    try:
        cosh_config_obj.scripts_d
    except AttributeError:
        LOG.debug("no scripts_d attribute")
        return
    glob_scripts = u'{:s}/*'.format(cosh_config_obj.scripts_d)

    for s_filename in glob.glob(glob_scripts):
        if s_filename.endswith("~"):
            continue
        if not os.access(s_filename, os.X_OK):
            continue
        command = u'{s_filename} {coshfile}'.format(
            s_filename=s_filename, coshfile=cosh_config_obj.coshfile)
        LOG.info(" {!s}".format(command))
        command_rc = subprocess.call(command, shell=True)
        LOG.info("# RC={!s}".format(command_rc))


def _onchange(cosh_config_obj):
    for func in cosh_config_obj.onchange:
        # LOG.debug("About to call {:s}".format(func))
        try:
            globals()[func](cosh_config_obj)
        except KeyError:
            LOG.warning("non-existing function {!r}. IGNORED.".format(func))


def watch(cosh_config_obj):
    root = cosh_config_obj.watched_root
    LOG.debug("Watching {!s}".format(root))
    inotifywait_call = '{binary} {args} "{folder}"'.format(
        binary=cosh_config_obj.inotifywait,
        args=' '.join(cosh_config_obj.inotifywait_args),
        folder=root)

    rc = subprocess.call(inotifywait_call, shell=True)
    while rc == 0:
        _onchange(cosh_config_obj)
        rc = subprocess.call(inotifywait_call, shell=True)


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

    if args.force_update:
        _onchange(cosh_cfg)
        sys.exit(0)

    try:
        watch(cosh_cfg)
    except KeyboardInterrupt:
        LOG.info("\nAborted.")
