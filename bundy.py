#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

from coshed import bundy

if __name__ == '__main__':
    bundy.cli_stub()
