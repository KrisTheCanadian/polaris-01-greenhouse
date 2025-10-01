"""Data model: holds Modbus address map and provides helpers to read/write.

We centralize the register/coil indexes so other modules import from here.
Addressing is zero-based for pyModbusTCP.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar

from pyModbusTCP.server import DataBank

@dataclass(frozen=True)
class Addresses:
    # Input Registers (read-only measurements)
    IR_AIRFLOW: ClassVar[int] = 0      # scaled 0.1 m3/min
    IR_TEMPERATURE: ClassVar[int] = 1  # scaled 0.1 °C
    IR_HUMIDITY: ClassVar[int] = 2     # scaled 0.1 %RH
    IR_FAN_RPM: ClassVar[int] = 3      # raw RPM
    IR_FAN_STATE: ClassVar[int] = 4    # 0=off,1=low,2=high

    # Holding Registers (config/setpoints)
    HR_AIRFLOW_SP: ClassVar[int] = 0
    HR_TEMPERATURE_SP: ClassVar[int] = 1
    HR_FAN_MODE_CMD: ClassVar[int] = 2  # 0=off,1=low,2=high (optional override)
    HR_FAN_RPM_SP: ClassVar[int] = 3
    HR_SIM_ENABLE: ClassVar[int] = 4

    # Coils (writable boolean commands)
    COIL_FAN_ENABLE: ClassVar[int] = 0
    COIL_FAN_HIGH_REQ: ClassVar[int] = 1
    COIL_ALARM_RESET: ClassVar[int] = 2

    # Discrete Inputs (read-only boolean status)
    DI_FAN_FAULT: ClassVar[int] = 0
    DI_FILTER_DIRTY: ClassVar[int] = 1
    DI_FAN_RUNNING: ClassVar[int] = 2


class DataModel:
    """Owns initialization and provides semantic getters/setters.

    This keeps other modules from directly poking DataBank with magic numbers.

    Accepts an optional existing `DataBank` (e.g. the one inside a ModbusServer)
    so external code can share the same backing data. If none is supplied a
    fresh DataBank is created.
    """

    def __init__(self, data_bank: DataBank | None = None):
        self._db = data_bank or DataBank()
        self._init_banks()
        self._init_defaults()

    # --- initialization -------------------------------------------------
    def _init_banks(self):
        # Pre-size with a buffer for future growth
        self._db.set_input_registers(0, [0] * 32)
        # holding registers (use instance API; class method set_words is deprecated)
        self._db.set_holding_registers(0, [0] * 32)
        self._db.set_coils(0, [False] * 16)
        self._db.set_discrete_inputs(0, [False] * 16)

    def _init_defaults(self):
        # Setpoints (scaled as defined above)
        self.write_holding(Addresses.HR_AIRFLOW_SP, 250)       # 25.0 m3/min
        self.write_holding(Addresses.HR_TEMPERATURE_SP, 225)   # 22.5 °C
        self.write_holding(Addresses.HR_FAN_MODE_CMD, 0)
        self.write_holding(Addresses.HR_FAN_RPM_SP, 900)
        self.write_holding(Addresses.HR_SIM_ENABLE, 1)
        self.write_coil(Addresses.COIL_FAN_ENABLE, True)

    # --- generic helpers ------------------------------------------------
    def read_input(self, addr: int) -> int:
        vals = self._db.get_input_registers(addr, 1)
        if not vals:
            raise IndexError(f"Input register address out of range: {addr}")
        return vals[0]

    def write_input(self, addr: int, value: int):
        self._db.set_input_registers(addr, [value])

    def read_holding(self, addr: int) -> int:
        vals = self._db.get_holding_registers(addr, 1)
        if not vals:
            raise IndexError(f"Holding register address out of range: {addr}")
        return vals[0]

    def write_holding(self, addr: int, value: int):
        self._db.set_holding_registers(addr, [value])

    def read_coil(self, addr: int) -> bool:
        vals = self._db.get_coils(addr, 1)
        if not vals:
            raise IndexError(f"Coil address out of range: {addr}")
        return vals[0]

    def write_coil(self, addr: int, value: bool):
        self._db.set_coils(addr, [value])

    def read_di(self, addr: int) -> bool:
        vals = self._db.get_discrete_inputs(addr, 1)
        if not vals:
            raise IndexError(f"Discrete input address out of range: {addr}")
        return vals[0]

    def write_di(self, addr: int, value: bool):
        self._db.set_discrete_inputs(addr, [value])

    # --- semantic convenience API ---------------------------------------
    def get_sim_enabled(self) -> bool:
        return self.read_holding(Addresses.HR_SIM_ENABLE) == 1

    def get_fan_mode_cmd(self) -> int:
        return self.read_holding(Addresses.HR_FAN_MODE_CMD)

    def get_fan_rpm_sp(self) -> int:
        return self.read_holding(Addresses.HR_FAN_RPM_SP)

    def fan_enable(self) -> bool:
        return self.read_coil(Addresses.COIL_FAN_ENABLE)

    def fan_high_requested(self) -> bool:
        return self.read_coil(Addresses.COIL_FAN_HIGH_REQ)

    def set_fan_state(self, state: int):
        self.write_input(Addresses.IR_FAN_STATE, state)
        # DI fan running bit: true if state>0
        self.write_di(Addresses.DI_FAN_RUNNING, state > 0)

    def set_airflow(self, value_scaled: int):
        self.write_input(Addresses.IR_AIRFLOW, value_scaled)

    def set_temperature(self, value_scaled: int):
        self.write_input(Addresses.IR_TEMPERATURE, value_scaled)

    def set_humidity(self, value_scaled: int):
        self.write_input(Addresses.IR_HUMIDITY, value_scaled)

    def set_fan_rpm(self, rpm: int):
        self.write_input(Addresses.IR_FAN_RPM, rpm)

    def set_fault(self, fault: bool):
        self.write_di(Addresses.DI_FAN_FAULT, fault)

    def set_filter_dirty(self, dirty: bool):
        self.write_di(Addresses.DI_FILTER_DIRTY, dirty)

    def consume_alarm_reset(self) -> bool:
        if self.read_coil(Addresses.COIL_ALARM_RESET):
            self.write_coil(Addresses.COIL_ALARM_RESET, False)
            return True
        return False
