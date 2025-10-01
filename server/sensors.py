"""Sensor simulation for airflow, temperature, humidity.

Creates plausible values tied to fan state.
"""
from __future__ import annotations
import random
from dataclasses import dataclass

from .data_model import DataModel, Addresses
from .fan import FanController


@dataclass
class SensorSimulator:
    model: DataModel
    fan: FanController

    def update(self):
        if not self.model.get_sim_enabled():
            return

        state = self.model.read_input(Addresses.IR_FAN_STATE)

        # Temperature: base 22.5C modified by fan cooling effect
        base = 225  # 22.5C scaled x10
        delta = 30 if state == 0 else -5 * state
        temp = base + delta + random.randint(-2, 2)
        temp = max(150, min(300, temp))
        self.model.set_temperature(temp)

        # Humidity: around 50% RH
        humidity = 500 + random.randint(-10, 10)
        self.model.set_humidity(humidity)

        # Airflow target by speed
        if state == 0:
            airflow_target = 0
        elif state == 1:
            airflow_target = 200  # 20.0
        else:
            airflow_target = 350  # 35.0
        airflow_actual = max(0, airflow_target + random.randint(-5, 5))
        self.model.set_airflow(airflow_actual)

        # Filter dirty status: running but low airflow
        dirty = state > 0 and airflow_actual < 100
        self.model.set_filter_dirty(dirty)
