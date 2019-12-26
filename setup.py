#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
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
    install_requires=[
        "beautifulsoup4>=4.6.0",
        "requests>=2.13.0",
        "pendulum==2.0.5",
        "future==0.18.2",
        "six==1.13.0",
        "Jinja2==2.10.3",
        "Flask==1.1.1",
    ],
    scripts=['coshed-watcher.py'],
    entry_points={
        'console_scripts': [
            'coshed-bundy = coshed.bundy:cli_stub',
            'coshed-wolfication = coshed.wolfication:cli_stub',
        ]
    }
)
