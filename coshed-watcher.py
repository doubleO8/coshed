#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import logging
import argparse

import coshed
from coshed.defaults import COSH_FILE_DEFAULT
from coshed.defaults import COSHED_CONFIG_DEFAULTS, ENV_MAP
from coshed.coshed_config import CoshedConfig
from coshed.coshed_watcher import CoshedWatcher

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

LOG = logging.getLogger("coshed_watcher")

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
        defaults=COSHED_CONFIG_DEFAULTS,
        coshfile=args.coshfile,
        environ_key_mapping=ENV_MAP,
    )

    LOG.warning("inotifywait and scss binaries need to be installed!")
    LOG.warning(
        " 'apt-get install inotify-tools ruby-sass' on debian "
        "derived distributions")
    LOG.warning("For JavaScript minification css-html-js-minify "
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
