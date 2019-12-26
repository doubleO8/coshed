#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
from builtins import object
import os
import uuid
import tempfile
import hashlib
import functools
import shutil
import subprocess
import logging
import codecs

from .defaults import CSS_HTML_JS_MINIFY_BINARY, CLOSURE_COMPILER_BINARY

#: call css-html-js-minify for creating <filename_trunk>.min.js
CSS_HTML_JS_MINIFY_CALL = '{binary} "{filename}"'

CLOSURE_COMPILER_CALL = '{binary} --compilation_level {compilation_level} ' \
                        '"{filename}" --js_output_file "{js_output_file}"'

class CoshedConcat(object):
    def __init__(self, filenames, trunk_template, **kwargs):
        self.sources = filenames
        self.target_folder = os.path.dirname(trunk_template)
        self.raise_on_bad_source = kwargs.get("raise_on_bad_source", False)
        self.tmp = tempfile.mkdtemp()
        self.uuid_value = uuid.uuid4().hex
        (self.trunk, _, self.ext) = os.path.basename(
            trunk_template).rpartition('.')
        self.tmp_filename = '{:s}.{:s}'.format(self.uuid_value, self.ext)
        self.tmp_target = os.path.join(self.tmp, self.tmp_filename)
        self.hexdigest = '0' * 16
        self.log = logging.getLogger(__name__)

    def _concat(self):
        items = 0
        self.hexdigest = '0' * 16

        if not self.sources:
            self.log.warning("No sources, no gain.")
            return 0

        with codecs.open(self.tmp_target, "wb", "utf-8") as tgt:
            for filename in self.sources:
                with codecs.open(filename, "rb", "utf-8") as src:
                    items += 1
                    for chunk in iter(functools.partial(src.read, 4096), ''):
                        tgt.write(chunk)

        return items

    def _mangle(self):
        raise NotImplementedError

    def mangle(self):
        try:
            self._mangle()
        except NotImplementedError:
            pass

    def get_target_filename(self):
        """

        Returns:

        >>> cc = CoshedConcat([], "concat.js")
        >>> cc.filename
        'concat.0000000000000000.js'
        """
        extension = ''
        if not self.trunk:
            raise ValueError("trunk may not be empty")
        if self.ext:
            extension = '.' + self.ext

        target_filename = '{trunk}.{hexdigest}{extension}'.format(
            trunk=self.trunk, hexdigest=self.hexdigest, extension=extension)
        return target_filename

    filename = property(get_target_filename)

    def write(self):
        if not self.sources:
            self.log.warning("No sources, no gain.")
            return None

        self._concat()
        self.mangle()
        hasher = hashlib.new("sha256")
        with codecs.open(self.tmp_target, "rb", "utf-8") as src:
            for chunk in iter(functools.partial(src.read, 4096), ''):
                hasher.update(chunk)
        self.hexdigest = hasher.hexdigest()
        target = os.path.join(self.target_folder, self.filename)

        try:
            shutil.copy(self.tmp_target, target)
        except IOError:
            self.log.info("Could not copy {!r} to {!r}".format(
                self.tmp_target, target))
            self.log.info("Trying to create {!r}".format(self.target_folder))
            os.makedirs(self.target_folder)
            shutil.copy(self.tmp_target, target)

        return os.path.abspath(target)

class CoshedConcatMinifiedJS(CoshedConcat):
    def __init__(self, filenames, trunk_template, **kwargs):
        CoshedConcat.__init__(self, filenames, trunk_template, **kwargs)
        self.log = logging.getLogger(__name__)
        self.css_html_js_minify_binary = kwargs.get('css_html_js_minify',
                                                    CSS_HTML_JS_MINIFY_BINARY)

    def _mangle(self):
        """

        Returns:

        >>> a = os.path.abspath(os.path.join(os.path.dirname(__file__), '../contrib/html_example/js/eins.js'))
        >>> b = os.path.abspath(os.path.join(os.path.dirname(__file__), '../contrib/html_example/js/two.js'))
        >>> ccm = CoshedConcatMinifiedJS([a, b], "/tmp/concat.js")
        >>> ccm.write()
        '/tmp/concat.45ddc7106b8125a4549590566570119675f6c8cd54ae03369b8c6e74e4e6c6cb.js'
        >>> ccm.hexdigest
        '45ddc7106b8125a4549590566570119675f6c8cd54ae03369b8c6e74e4e6c6cb'
        """
        out_filename = '{:s}.min.{:s}'.format(self.uuid_value, self.ext)
        out_target = os.path.join(self.tmp, out_filename)

        minime = CSS_HTML_JS_MINIFY_CALL.format(
            binary=self.css_html_js_minify_binary, filename=self.tmp_target)
        rc = subprocess.call(minime, shell=True)

        if os.path.exists(out_target):
            self.tmp_target = out_target

        return rc


class CoshedConcatClosure(CoshedConcat):
    def __init__(self, filenames, trunk_template, **kwargs):
        CoshedConcat.__init__(self, filenames, trunk_template, **kwargs)
        self.log = logging.getLogger(__name__)
        self.closure_binary = kwargs.get('closure_binary',
                                         CLOSURE_COMPILER_BINARY)
        self.compilation_level = kwargs.get("compilation_level",
                                            "SIMPLE_OPTIMIZATIONS")

    def _mangle(self):
        """

        Returns:

        >>> a = os.path.abspath(os.path.join(os.path.dirname(__file__), '../contrib/html_example/js/eins.js'))
        >>> b = os.path.abspath(os.path.join(os.path.dirname(__file__), '../contrib/html_example/js/two.js'))
        >>> ccm = CoshedConcatClosure([a, b], "/tmp/concat.js")
        >>> ccm.write()
        '/tmp/concat.0a72b7a757548899130fb9ef1bb49d7ec4b7c9683b8bd006404e833c37f6b0d7.js'
        >>> ccm.hexdigest
        '0a72b7a757548899130fb9ef1bb49d7ec4b7c9683b8bd006404e833c37f6b0d7'
        """
        out_filename = '{:s}.min.{:s}'.format(self.uuid_value, self.ext)
        out_target = os.path.join(self.tmp, out_filename)

        minime = CLOSURE_COMPILER_CALL.format(
            binary=self.closure_binary, filename=self.tmp_target,
            js_output_file=out_target,
            compilation_level=self.compilation_level)
        rc = subprocess.call(minime, shell=True)

        if os.path.exists(out_target):
            self.tmp_target = out_target

        return rc

if __name__ == '__main__':
    import doctest

    (FAILED, SUCCEEDED) = doctest.testmod()
    print("[doctest] SUCCEEDED/FAILED: {:d}/{:d}".format(SUCCEEDED, FAILED))
