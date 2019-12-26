#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json


def load_json(path):
    with open(path, "r") as src:
        content = json.load(src)

    return content
