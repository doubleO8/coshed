#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import logging
import argparse

from coshed.coshed_config import CoshedConfig, COSH_FILE_DEFAULT

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

LOG = logging.getLogger("coshed_watcher")

PROJECT_ROOT = os.getcwd()

SCSS_ROOT = os.path.join(PROJECT_ROOT, 'sourcefiles/scss')

CSS_ROOT = os.path.join(PROJECT_ROOT, 'plugin/public/css')

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
    # root path being watched by inotifywait
    watched_root=SCSS_ROOT,
    #: source (SCSS) -> target (CSS) locations
    scss_map=[
        (
            os.path.join(SCSS_ROOT, "style.scss"),
            os.path.join(CSS_ROOT, "style.min.css")
        ),
        (
            os.path.join(SCSS_ROOT, "theme/original.scss"),
            os.path.join(CSS_ROOT, "theme_original.css")
        ),
        (
            os.path.join(SCSS_ROOT, "theme/original-small-screen.scss"),
            os.path.join(CSS_ROOT, "../themes/original-small-screen.css")
        ),
    ],
    #: default locations of used binaries
    inotifywait="inotifywait",
    scss="scss",
    #: functions to be called when a change in *watched_root* is detected
    onchange=["call_scss"]
)


def call_scss(cosh_config_obj):
    for (src, dst) in cosh_config_obj.scss_map:
        scss_call = '{binary} {args} "{src}":"{dst}"'.format(
            binary=cosh_config_obj.scss,
            args=' '.join(cosh_config_obj.scss_args),
            src=src, dst=dst)
        LOG.info(" {!s}".format(scss_call))
        scss_rc = subprocess.call(scss_call, shell=True)
        LOG.info("# RC={!s}".format(scss_rc))


def watch(cosh_config_obj):
    root = cosh_config_obj.watched_root
    LOG.debug("Watching {!s}".format(root))
    inotifywait_call = "{binary} -r -e modify {folder}".format(
        binary=cosh_config_obj.inotifywait, folder=root)

    rc = subprocess.call(inotifywait_call, shell=True)
    while rc == 0:
        for func in cosh_config_obj.onchange:
            LOG.info("About to run: {:s}".format(func))
            try:
                globals()[func](cosh_config_obj)
            except KeyError:
                LOG.warning("non-existing function..")

        rc = subprocess.call(inotifywait_call, shell=True)


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
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
            "override used binary {key!r}.".format(
                env_key=env_key, key=key))

    if args.verbose > 0:
        LOG.debug("Supported S/CSS transformations:")
        for (src, dst) in cosh_cfg.scss_map:
            LOG.debug("{!r} -> {!r}".format(src, dst))

    if args.verbose > 1:
        LOG.info("coshed configuration:")
        LOG.info(cosh_cfg)

    if args.force_update:
        call_scss(cosh_cfg)
        sys.exit(0)

    try:
        watch(cosh_cfg)
    except KeyboardInterrupt:
        LOG.info("\nAborted.")
