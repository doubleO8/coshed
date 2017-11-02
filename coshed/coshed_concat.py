#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import uuid
import tempfile
import hashlib
import functools
import shutil
import subprocess


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

    def _concat(self):
        self.hexdigest = '0' * 16
        with open(self.tmp_target, "wb") as tgt:
            for filename in self.sources:
                with open(filename, "rb") as src:
                    for chunk in iter(functools.partial(src.read, 4096), ''):
                        tgt.write(chunk)

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
        self._concat()
        self.mangle()
        hasher = hashlib.new("sha256")
        with open(self.tmp_target, "rb") as src:
            for chunk in iter(functools.partial(src.read, 4096), ''):
                hasher.update(chunk)
        self.hexdigest = hasher.hexdigest()
        target = os.path.join(self.target_folder, self.filename)
        shutil.copy(self.tmp_target, target)
        return os.path.abspath(target)


class CoshedConcatMinifiedJS(CoshedConcat):
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
        CMD_FMT = '{binary} "{filename}"'
        out_filename = '{:s}.min.{:s}'.format(self.uuid_value, self.ext)
        out_target = os.path.join(self.tmp, out_filename)

        minime = CMD_FMT.format(binary="css-html-js-minify.py",
                                filename=self.tmp_target)
        rc = subprocess.call(minime, shell=True)
        self.tmp_target = out_target
        return rc


if __name__ == '__main__':
    import doctest

    (FAILED, SUCCEEDED) = doctest.testmod()
    print("[doctest] SUCCEEDED/FAILED: {:d}/{:d}".format(SUCCEEDED, FAILED))
