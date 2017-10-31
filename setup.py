#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup
import versioneer

setup(
    name='coshed',
    author="doubleO8",
    author_email="wb008@hdm-stuttgart.de",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='Project deployment and distribution tools for lazy developers',
    long_description="",
    url="https://github.com/doubleO8/coshed",
    packages=['coshed'],
    scripts=['coshed-watcher.py']
)
