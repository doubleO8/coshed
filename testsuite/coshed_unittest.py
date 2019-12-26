#!/usr/bin/env python
# -*- coding: utf-8 -*-
from builtins import object
import sys
import os
import tempfile
import json
import codecs

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


class CoshedTestCaseParts(object):
    _tmp = tempfile.mkdtemp("_coshed")

    def tempfile_name(self, rel_path):
        return os.path.join(self._tmp, rel_path)

    def load_json(self, path):
        with codecs.open(path, "rb", "utf-8") as src:
            return json.load(src)