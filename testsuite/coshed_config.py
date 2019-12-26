#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import unittest
import uuid

from .coshed_unittest import CoshedTestCaseParts
from coshed.coshed_config import CoshedConfig


class NoCoshConfigfileTestCase(unittest.TestCase, CoshedTestCaseParts):
    def setUp(self):
        self.defaults = dict(
            file="x.txt",
            value=42
        )
        self.coshfile = self.tempfile_name(
            uuid.uuid4().hex + '_melli-einfach.json')
        self.cfg = CoshedConfig(ro=True, defaults=self.defaults,
                                coshfile=self.coshfile)

    def test_defaults(self):
        self.assertEqual(42, self.cfg.value)
        self.assertEqual("x.txt", self.cfg.file)
        self.assertEqual(self.coshfile, self.cfg.coshfile)
        self.assertFalse(os.path.isfile(self.cfg.coshfile))

    def test_write_coshfile(self):
        self.assertEqual(self.coshfile, self.cfg.coshfile)
        self.cfg.write()
        self.assertFalse(os.path.isfile(self.cfg.coshfile))

    def test_forced_write_coshfile(self):
        self.assertEqual(self.coshfile, self.cfg.coshfile)
        self.cfg.write(force=True)
        self.assertTrue(os.path.isfile(self.cfg.coshfile))
        file_data = self.load_json(self.cfg.coshfile)
        self.assertDictEqual(self.defaults, file_data)


class CoshConfigfileTestCase(unittest.TestCase, CoshedTestCaseParts):
    def setUp(self):
        self.defaults = dict(
            file="yz.txt",
            value=99
        )
        self.coshfile = self.tempfile_name(
            uuid.uuid4().hex + '_afrob-einfach.json')
        self.cfg = CoshedConfig(ro=False, defaults=self.defaults,
                                coshfile=self.coshfile)

    def test_defaults(self):
        self.assertEqual(99, self.cfg.value)
        self.assertEqual("yz.txt", self.cfg.file)
        self.assertEqual(self.coshfile, self.cfg.coshfile)
        self.assertTrue(os.path.isfile(self.cfg.coshfile))

    def test_read_coshfile(self):
        self.assertEqual(self.coshfile, self.cfg.coshfile)
        self.assertTrue(os.path.isfile(self.cfg.coshfile))
        file_data = self.load_json(self.cfg.coshfile)
        self.assertDictEqual(self.defaults, file_data)


class CoshConfigfileAndEnvironTestCase(unittest.TestCase, CoshedTestCaseParts):
    def setUp(self):
        os.environ["FERRIS_AFROB"] = "Reimemonster"
        env_mapping = [
            ("FERRIS_AFROB", "afrob_and_ferris"),
        ]
        self.defaults = dict(
            file="huch.xml",
            value=1234
        )
        self.coshfile = self.tempfile_name(
            uuid.uuid4().hex + '_feddich.json')
        self.cfg = CoshedConfig(defaults=self.defaults,
                                coshfile=self.coshfile,
                                environ_key_mapping=env_mapping)

    def test_defaults(self):
        self.assertEqual(1234, self.cfg.value)
        self.assertEqual("huch.xml", self.cfg.file)
        self.assertEqual(self.coshfile, self.cfg.coshfile)
        self.assertTrue(os.path.isfile(self.cfg.coshfile))

    def test_read_coshfile(self):
        self.assertEqual("Reimemonster", self.cfg.afrob_and_ferris)
        self.assertEqual(self.coshfile, self.cfg.coshfile)
        self.assertTrue(os.path.isfile(self.cfg.coshfile))
        file_data = self.load_json(self.cfg.coshfile)
        self.assertDictContainsSubset(self.defaults, file_data)


class EmptyTestCase(unittest.TestCase, CoshedTestCaseParts):
    def setUp(self):
        self.cfg = CoshedConfig()

    def test_defaults(self):
        self.assertEqual([], list(self.cfg.keys()))
        self.assertFalse(os.path.isfile(self.cfg.coshfile))

    def test_read_altered_coshfile(self):
        self.cfg["x"] = 123
        self.cfg.write()
        self.assertTrue(os.path.isfile(self.cfg.coshfile))
        file_data = self.load_json(self.cfg.coshfile)
        expected = dict(x=123)
        self.assertDictEqual(expected, file_data)


if __name__ == '__main__':
    unittest.main()
