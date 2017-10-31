#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


class CoshedTestCaseParts(object):
    _tmp = tempfile.mkdtemp("_coshed")

    def tempfile_name(self, rel_path):
        return os.path.join(self._tmp, rel_path)

    def load_json(self, path):
        with open(path, "rb") as src:
            return json.load(src)