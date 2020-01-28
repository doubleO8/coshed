#!/usr/bin/env python
# -*- coding: utf-8 -*-


from builtins import str
from past.builtins import basestring


def to_unicode_or_bust(obj, encoding='utf-8'):
    """
    Convert string *obj* to unicode.
    *obj* is left alone if it is not string instance.
    If *obj* cannot be converted some sort of exception is thrown.

    Args:
        obj (basestring): string to convert
        encoding (str): Target encoding
    """
    if isinstance(obj, basestring):
        if not isinstance(obj, str):
            obj = str(obj, encoding)
    return obj
