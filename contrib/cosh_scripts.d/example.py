#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from coshed.coshed_config import CoshedConfigReadOnly

print("Example called with {!r}".format(sys.argv))
coshfile = sys.argv[1]

cosh_cfg = CoshedConfigReadOnly(coshfile)

print("configuration values defined in {!r}".format(cosh_cfg.coshfile))

for key, value in cosh_cfg.kv_pairs():
    print("{:20s}: {!r}".format(key, value))
