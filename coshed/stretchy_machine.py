#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import pendulum

try:
    from transitions import Machine
except ImportError:
    print("I need the transitions package but will fail later.")

STATE_S0 = "s0"
STATE_OPEN = "open"
STATE_CLOSED = "closed"
STATE_DEAD = "dead"


class StretchyMachineException(Exception):
    pass


class StretchyMachineStillAlive(StretchyMachineException):
    pass


class StretchyMachine(Machine):
    def dump_state_of_the_onion(self):
        self.log.debug(
            "state={state:6s} current_value={current_value!s:16} "
            "#dt_objects={dt_objects_len:5d} #periods={periods_len:5d}".format(
                state=self.state,
                current_value=self.current_value,
                dt_objects_len=len(self.dt_objects),
                periods_len=len(self.periods),
            )
        )

    def on_enter_open(self, *args, **kwargs):
        self.log.debug("ENTER OPEN")
        self.current_value = kwargs.get(self.value_key)
        dt_object = kwargs.get(self.dt_key)

        if dt_object:
            self.log.debug(
                "+ {!r:10} {!r}".format(self.current_value, dt_object)
            )

            if len(self.dt_objects):
                if dt_object <= self.dt_objects[-1]:
                    self.log.warning(
                        "{!r} <= {!r}".format(dt_object, self.dt_objects[-1])
                    )
            self.dt_objects.append(dt_object)

        self.dump_state_of_the_onion()
        self.log.debug("")

    def on_exit_open(self, *args, **kwargs):
        self.log.debug("# EXIT OPEN")
        self.overhang_dt_object = kwargs.get(self.dt_key)
        if self.overhang_dt_object:
            self.log.debug(
                "= {!r:10} {!r}".format(
                    self.current_value, self.overhang_dt_object
                )
            )

    def _terminate_period(self):
        try:
            current_p = pendulum.Period(
                self.dt_objects[0], self.dt_objects[-1]
            )
            self.periods.append((current_p, self.current_value))
        except Exception as exc:
            self.log.debug(exc)

        self.dt_objects = []

    def on_enter_dead(self, *args, **kwargs):
        self.log.debug("DEAD")
        self._terminate_period()
        self.periods = sorted(self.periods)
        self.dump_state_of_the_onion()

    def on_exit_closed(self, *args, **kwargs):
        self.log.debug("EXIT CLOSED")
        self.log.debug("~" * 80)
        self.dump_state_of_the_onion()
        self._terminate_period()
        self.current_value = kwargs.get(self.value_key)

        if self.overhang_dt_object:
            self.log.debug(
                "! {!r:10} {!r}".format(
                    self.current_value, self.overhang_dt_object
                )
            )
            self.dt_objects.append(self.overhang_dt_object)
            self.overhang_dt_object = None

        self.log.debug("v" * 80)
        self.dump_state_of_the_onion()
        self.log.debug("")

    def changed_value(self, *args, **kwargs):
        is_changed = self.current_value != kwargs.get(self.value_key)
        return is_changed

    def same_value(self, *args, **kwargs):
        return not self.changed_value(*args, **kwargs)

    def have_payload(self, *args, **kwargs):
        for key in self.required_payload_keys:
            try:
                kwargs[key]
            except KeyError:
                return False

        return True

    def yield_stretches_with(self, value, auto_terminate=True):
        if self.state != STATE_DEAD:
            if auto_terminate:
                self.terminate()
            else:
                raise StretchyMachineStillAlive("I am not terminated!")

        for (period, p_value) in self.periods:
            if p_value == value:
                yield period

    def __init__(self, *args, **kwargs):
        states = [STATE_S0, STATE_OPEN, STATE_CLOSED, STATE_DEAD]

        Machine.__init__(self, states=states, initial=STATE_S0)
        self.log = logging.getLogger(__name__)
        self.periods = []
        self.dt_objects = []
        self.current_value = None
        self.overhang_dt_object = None
        self.dt_key = kwargs.get("dt_key", "dt")
        self.value_key = kwargs.get("value_key", "value")
        self.required_payload_keys = (self.dt_key, self.value_key)

        self.add_transition(
            "shovel", STATE_S0, STATE_OPEN, conditions=["have_payload"]
        )

        self.add_transition("terminate", "*", STATE_DEAD)

        self.add_transition(
            "shovel",
            STATE_OPEN,
            STATE_CLOSED,
            conditions=["have_payload", "changed_value"],
        )

        self.add_transition(
            "shovel",
            STATE_OPEN,
            STATE_OPEN,
            conditions=["have_payload", "same_value"],
        )

        self.add_transition(
            "shovel",
            STATE_CLOSED,
            STATE_OPEN,
            conditions=["have_payload", "changed_value"],
        )


if __name__ == "__main__":
    logging.basicConfig(
        # level=logging.DEBUG,
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y%m%d %H:%M:%S",
    )

    logging.getLogger("transitions").setLevel(logging.FATAL)
    m = StretchyMachine()

    # m.terminate()
    for x in range(1, 4):
        m.shovel(value=True, dt=pendulum.DateTime(2020, 1, 1, 0, 0, x))
        # m.shovel(value=True, dt=pendulum.DateTime(2020, 1, 1, 0, 0, x-1))
        m.dump_state_of_the_onion()

    for x in range(3):
        m.shovel(value=False, dt=pendulum.DateTime(2020, 1, 2, 0, 0, x))
        m.dump_state_of_the_onion()

    m.terminate()
    print(list(m.yield_stretches_with(True)))
