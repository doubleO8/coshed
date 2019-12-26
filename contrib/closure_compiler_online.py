#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import requests

# https://developers.google.com/closure/compiler/docs/api-tutorial1

with open(sys.argv[1], 'rb') as src:
    js_code = src.read()

data = {
    "output_format": "text",
    "compilation_level": "SIMPLE_OPTIMIZATIONS",
    "output_info": "compiled_code",
    "js_code": js_code
}

req = requests.post('https://closure-compiler.appspot.com/compile', data=data)
print(req.text)
