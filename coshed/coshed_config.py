#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import argparse

COSH_FILE_DEFAULT = 'cosh.json'


class CoshedConfig(object):
    """
    Simple Configuration object:

        * settings may be stored in a JSON file
        * access settings by attribute or key
        * default values may be set by `dict()`, kwargs and environment variables

    """
    def __init__(self, *args, **kwargs):
        self._data_sources = {
            'environ': dict(),
            'config': dict()
        }
        self._sources_log = []
        self._key_set = None
        key_set = kwargs.get("keys")
        if key_set and isinstance(key_set, set):
            self._key_set = key_set
        coshfile = kwargs.get("coshfile")
        self._ro = kwargs.get("ro", False)
        defaults = kwargs.get("defaults", {})
        environ_key_mapping = kwargs.get("environ_key_mapping", [])

        for source_value in args:
            if isinstance(source_value, argparse.Namespace):
                self._data_sources["args"] = vars(source_value)
            else:
                if coshfile is None:
                    try:
                        # value might be string qualifying for a path value
                        source_value.startswith("-")
                        coshfile = source_value
                    except Exception:
                        pass

        for key in kwargs:
            if key in (
                    'defaults', 'coshfile', 'ro', 'keys',
                    'environ_key_mapping'):
                continue
            source_value = kwargs[key]
            defaults[key] = source_value

        self._data_sources["defaults"] = defaults

        if coshfile is None:
            self._coshfile = COSH_FILE_DEFAULT
        else:
            self._coshfile = os.path.abspath(coshfile)

        if os.path.isfile(self._coshfile):
            with open(self._coshfile, "rb") as src:
                try:
                    self._data_sources["config"] = json.load(src)
                except ValueError:
                    pass

        for env_key, key in environ_key_mapping:
            try:
                self._data_sources["environ"][key] = os.environ[env_key]
            except KeyError:
                pass

        self._populate()
        self.write()

    def _acceptable_attr_name(self, attr_name):
        if attr_name.startswith('_') or attr_name == 'coshfile':
            return False
        if self._key_set:
            if not attr_name in self._key_set:
                return False
        if hasattr(self, attr_name) and callable(getattr(self, attr_name)):
            return False

        return True

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, item):
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError(item)

    def _populate(self):
        self._sources_log = []
        source_order = ('args', 'environ', 'config', 'defaults')
        key_set = set()

        if self._key_set:
            key_set = self._key_set
        else:
            for source_key in source_order:
                try:
                    key_set |= set(self._data_sources[source_key].keys())
                except KeyError:
                    pass

        for key in key_set:
            if not self._acceptable_attr_name(key):
                continue

            for source_key in source_order:
                try:
                    value = self._data_sources[source_key][key]
                    setattr(self, key, value)
                    self._sources_log.append(
                        '{:s}={!r} defined by {:s}'.format(key, value,
                                                           source_key.upper()))
                    break
                except KeyError:
                    pass

    def _data_dict(self):
        data = dict()
        for key in self.keys():
            data[key] = self[key]
        return data

    def get_filename(self):
        return os.path.abspath(self._coshfile)

    coshfile = property(get_filename)

    def write(self, force=False):
        if self._ro and not force:
            return
        data = self._data_dict()

        if not data:
            return

        if self._data_sources["config"] == data:
            return

        with open(self._coshfile, "wb") as tgt:
            json.dump(data, tgt, indent=2)

    def keys(self):
        for attr_name in dir(self):
            if self._acceptable_attr_name(attr_name):
                yield attr_name

    def kv_pairs(self):
        for key in self.keys():
            value = getattr(self, key)
            yield key, value

    def __str__(self):
        items = list()
        for attr_name in self.keys():
            items.append((attr_name, getattr(self, attr_name)))
        return '<{:s} {:s}>'.format(self.__class__.__name__, ' '.join(
            ['{:s}={!r}'.format(k, v) for k, v in sorted(items)]))

    def __repr__(self):
        return repr(self._data_dict())

class CoshedConfigReadOnly(CoshedConfig):
    def __init__(self, coshfile):
        CoshedConfig.__init__(self, ro=True, coshfile=coshfile)

    def write(self, *args, **kwargs):
        return False