#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    try:
        from importlib.metadata import version
    except ImportError:
        from importlib_metadata import version

    __version__ = version(__package__)
except Exception:
    __version__ = "0.0.999"
