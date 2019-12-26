#!/usr/bin/env python
# -*- coding: utf-8 -*-
from builtins import object
import os
import subprocess
import logging
import glob

from coshed.coshed_concat import CoshedConcatMinifiedJS, CoshedConcatClosure


class CoshedWatcher(object):
    def __init__(self, cosh_cfg):
        self.cosh_config_obj = cosh_cfg
        self.log = logging.getLogger(__name__)

    def call_scss(self):
        if not self.cosh_config_obj.scss_map:
            self.log.debug("Empty scss_map!")

        for (src, dst) in self.cosh_config_obj.scss_map:
            scss_call = '{binary} {args} "{src}":"{dst}"'.format(
                binary=self.cosh_config_obj.scss,
                args=' '.join(self.cosh_config_obj.scss_args),
                src=src, dst=dst)
            self.log.info(" {!s}".format(scss_call))
            scss_rc = subprocess.call(scss_call, shell=True)
            self.log.info("# RC={!s}".format(scss_rc))

    def call_js(self):
        if not self.cosh_config_obj.concat_js_sources:
            self.log.debug("Empty concat_js_sources!")
        if self.cosh_config_obj.concat_js_compiler == 'closure':
            cat = CoshedConcatClosure(
                self.cosh_config_obj.concat_js_sources,
                self.cosh_config_obj.concat_js_trunk,
                closure_binary=self.cosh_config_obj.closure_compiler
            )
        else:
            cat = CoshedConcatMinifiedJS(
                self.cosh_config_obj.concat_js_sources,
                self.cosh_config_obj.concat_js_trunk,
                css_html_js_minify=self.cosh_config_obj.css_html_js_minify
            )
        cat.write()

    def call_scripts(self):
        try:
            self.cosh_config_obj.scripts_d
        except AttributeError:
            self.log.debug("no scripts_d attribute")
            return

        glob_scripts = u'{:s}/*'.format(self.cosh_config_obj.scripts_d)

        for s_filename in glob.glob(glob_scripts):
            if s_filename.endswith("~"):
                continue
            if os.path.basename(s_filename).startswith("OFF."):
                continue
            if not os.access(s_filename, os.X_OK):
                continue

            command = u'{s_filename} {coshfile}'.format(
                s_filename=s_filename, coshfile=self.cosh_config_obj.coshfile)
            self.log.info(" {!s}".format(command))
            command_rc = subprocess.call(command, shell=True)
            self.log.info("# RC={!s}".format(command_rc))

    def on_change(self):
        for func_name in self.cosh_config_obj.onchange:
            # self.log.debug("About to call {:s}".format(func))
            try:
                func = getattr(self, func_name)
                func()
            except AttributeError:
                self.log.warning(
                    "Missing method {!r}. IGNORED.".format(func_name))

    def watch(self):
        root = os.path.abspath(self.cosh_config_obj.watched_root)
        self.log.info("Watching {!s}".format(root))
        inotifywait_call = '{binary} {args} "{folder}"'.format(
            binary=self.cosh_config_obj.inotifywait,
            args=' '.join(self.cosh_config_obj.inotifywait_args),
            folder=root)

        rc = subprocess.call(inotifywait_call, shell=True)
        while rc == 0:
            self.on_change()
            rc = subprocess.call(inotifywait_call, shell=True)
