#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import unittest
import uuid

import pendulum

from coshed.stretchy_machine import StretchyMachine


class StretchyMachineTestCase(unittest.TestCase):
    def setUp(self):
        self.log = logging.getLogger(__name__)
        pass

    def test_two_periods(self):
        m = StretchyMachine()
        periods_in = [
            (
                pendulum.Period(
                    pendulum.DateTime(2020, 1, 1, 0, 0, 1),
                    pendulum.DateTime(2020, 1, 1, 0, 0, 11)
                ),
                "yes"
            ),
            (
                pendulum.Period(
                    pendulum.DateTime(2020, 2, 1, 0, 0, 1),
                    pendulum.DateTime(2020, 2, 1, 0, 0, 12)
                ),
                "no"
            ),
        ]

        for period, value in periods_in:
            for dt_object in period.range('seconds'):
                self.log.debug("> {!r:10} {!r}".format(value, dt_object))
                m.shovel(value=value, dt=dt_object)
        m.terminate()

        yes_periods = list(m.yield_stretches_with('yes'))
        self.assertEqual(1, len(yes_periods))
        self.assertEqual(10, yes_periods[0].total_seconds())

        no_periods = list(m.yield_stretches_with('no'))
        self.assertEqual(1, len(no_periods))
        self.assertEqual(11, no_periods[0].total_seconds())

    def test_three_periods(self):
        m = StretchyMachine()
        periods_in = [
            (
                pendulum.Period(
                    pendulum.DateTime(2020, 1, 1, 0, 0, 1),
                    pendulum.DateTime(2020, 1, 1, 0, 0, 11)
                ),
                "yes"
            ),
            (
                pendulum.Period(
                    pendulum.DateTime(2020, 2, 1, 0, 0, 1),
                    pendulum.DateTime(2020, 2, 1, 0, 0, 12)
                ),
                "no"
            ),
            (
                pendulum.Period(
                    pendulum.DateTime(2020, 2, 1, 0, 0, 1),
                    pendulum.DateTime(2020, 2, 1, 0, 0, 13)
                ),
                "yes"
            ),
        ]

        for period, value in periods_in:
            for dt_object in period.range('seconds'):
                self.log.debug("> {!r:10} {!r}".format(value, dt_object))
                m.shovel(value=value, dt=dt_object)

        yes_periods = list(m.yield_stretches_with('yes'))
        self.assertEqual(2, len(yes_periods))
        self.assertEqual(10, yes_periods[0].total_seconds())
        self.assertEqual(12, yes_periods[1].total_seconds())

        no_periods = list(m.yield_stretches_with('no'))
        self.assertEqual(1, len(no_periods))
        self.assertEqual(11, no_periods[0].total_seconds())


if __name__ == '__main__':
    logging.basicConfig(
        # level=logging.DEBUG,
        level=logging.INFO,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y%m%d %H:%M:%S')

    logging.getLogger('transitions').setLevel(logging.FATAL)
    unittest.main()
