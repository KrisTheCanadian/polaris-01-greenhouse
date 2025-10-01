"""Fan control and simple state simulation for a two-speed fan.

Determines the effective fan speed state based on enable, mode command and
optional 'high request' coil. Updates RPM and fault conditions.
"""
from __future__ import annotations
import random
from dataclasses import dataclass

from .data_model import DataModel


@dataclass
class FanController:
    model: DataModel

    def update(self):
        # Determine commanded mode
        if not self.model.fan_enable():
            state = 0
        else:
            mode_cmd = self.model.get_fan_mode_cmd()  # 0/1/2
            if mode_cmd in (1, 2):
                state = mode_cmd
            else:
                # fallback to coil request
                state = 2 if self.model.fan_high_requested() else 1
        self.model.set_fan_state(state)

        # RPM simulation derived from setpoint
        rpm_sp = self.model.get_fan_rpm_sp()
        if state == 0:
            rpm_actual = 0
        elif state == 1:
            rpm_actual = int(rpm_sp * 0.6) + random.randint(-10, 10)
        else:  # high
            rpm_actual = rpm_sp + random.randint(-15, 15)
        self.model.set_fan_rpm(max(0, rpm_actual))

        # Fault if commanded running but rpm too low
        fault = state > 0 and rpm_actual < 100
        self.model.set_fault(fault)

        # Filter dirty heuristic: airflow below threshold while running set later by sensor
        # Alarm reset coil could clear fault (example logic)
        if self.model.consume_alarm_reset():
            self.model.set_fault(False)
