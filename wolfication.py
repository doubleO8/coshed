#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from coshed import wolfication

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

if __name__ == '__main__':
    wolfication.cli_stub()
