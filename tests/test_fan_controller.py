import pytest
import random

from server.data_model import DataModel, Addresses
from server.fan import FanController


class MockRandom:
    """Deterministic random provider for tests."""
    def __init__(self, sequence=None):
        self.sequence = sequence or [0]
        self.index = 0
    
    def randint(self, a, b):
        """Mock random.randint with deterministic values"""
        if self.index >= len(self.sequence):
            self.index = 0  # Cycle through sequence
        value = self.sequence[self.index]
        self.index += 1
        return value


@pytest.fixture
def mock_random(monkeypatch):
    """Fixture to replace random.randint with deterministic values"""
    def _mock_random(sequence=None):
        mock = MockRandom(sequence)
        monkeypatch.setattr(random, "randint", mock.randint)
        return mock
    return _mock_random


def test_fan_off_when_disabled(mock_random):
    mock_random()  # Use default sequence [0]
    dm = DataModel()
    fan = FanController(dm)
    dm.write_coil(Addresses.COIL_FAN_ENABLE, False)

    fan.update()
    
    assert dm.read_input(Addresses.IR_FAN_STATE) == 0
    assert dm.read_input(Addresses.IR_FAN_RPM) == 0
    assert dm.read_di(Addresses.DI_FAN_FAULT) is False


def test_fan_low_mode_command(mock_random):
    mock_random()
    dm = DataModel()
    fan = FanController(dm)
    
    dm.write_coil(Addresses.COIL_FAN_ENABLE, True)
    dm.write_holding(Addresses.HR_FAN_MODE_CMD, 1)
    dm.write_holding(Addresses.HR_FAN_RPM_SP, 500)

    fan.update()
    
    assert dm.read_input(Addresses.IR_FAN_STATE) == 1
    assert dm.read_input(Addresses.IR_FAN_RPM) == 300  # 500 * 0.6 + 0
    assert dm.read_di(Addresses.DI_FAN_FAULT) is False


def test_fan_high_mode_command(mock_random):
    mock_random()
    dm = DataModel()
    fan = FanController(dm)
    
    dm.write_coil(Addresses.COIL_FAN_ENABLE, True)
    dm.write_holding(Addresses.HR_FAN_MODE_CMD, 2)
    dm.write_holding(Addresses.HR_FAN_RPM_SP, 800)

    fan.update()
    
    assert dm.read_input(Addresses.IR_FAN_STATE) == 2
    assert dm.read_input(Addresses.IR_FAN_RPM) == 800  # 800 + 0
    assert dm.read_di(Addresses.DI_FAN_FAULT) is False


def test_fan_high_from_coil_fallback(mock_random):
    mock_random()
    dm = DataModel()
    fan = FanController(dm)
    
    dm.write_coil(Addresses.COIL_FAN_ENABLE, True)
    dm.write_holding(Addresses.HR_FAN_MODE_CMD, 0)  # No mode command
    dm.write_coil(Addresses.COIL_FAN_HIGH_REQ, True)  # But high requested
    dm.write_holding(Addresses.HR_FAN_RPM_SP, 600)

    fan.update()
    
    assert dm.read_input(Addresses.IR_FAN_STATE) == 2  # Should be high
    assert dm.read_input(Addresses.IR_FAN_RPM) == 600  # 600 + 0
    assert dm.read_di(Addresses.DI_FAN_FAULT) is False


def test_fan_low_from_coil_fallback(mock_random):
    mock_random()
    dm = DataModel()
    fan = FanController(dm)
    
    dm.write_coil(Addresses.COIL_FAN_ENABLE, True)
    dm.write_holding(Addresses.HR_FAN_MODE_CMD, 0)  # No mode command
    dm.write_coil(Addresses.COIL_FAN_HIGH_REQ, False)  # Low requested
    dm.write_holding(Addresses.HR_FAN_RPM_SP, 500)

    fan.update()
    
    assert dm.read_input(Addresses.IR_FAN_STATE) == 1  # Should be low
    assert dm.read_input(Addresses.IR_FAN_RPM) == 300  # 500 * 0.6 + 0
    assert dm.read_di(Addresses.DI_FAN_FAULT) is False


def test_fan_fault_when_rpm_too_low(mock_random):
    mock_random()
    dm = DataModel()
    fan = FanController(dm)
    
    dm.write_coil(Addresses.COIL_FAN_ENABLE, True)
    dm.write_holding(Addresses.HR_FAN_MODE_CMD, 1)
    # Set RPM so low that 60% of it is below the fault threshold (100)
    dm.write_holding(Addresses.HR_FAN_RPM_SP, 160)  # 160 * 0.6 = 96

    fan.update()
    
    assert dm.read_input(Addresses.IR_FAN_STATE) == 1
    assert dm.read_input(Addresses.IR_FAN_RPM) == 96
    assert dm.read_di(Addresses.DI_FAN_FAULT) is True


def test_alarm_reset_clears_fault(mock_random):
    mock_random([0, 0])  # Need two zero values for two updates
    dm = DataModel()
    fan = FanController(dm)
    
    # Set up a fault condition
    dm.write_coil(Addresses.COIL_FAN_ENABLE, True)
    dm.write_holding(Addresses.HR_FAN_MODE_CMD, 1)
    dm.write_holding(Addresses.HR_FAN_RPM_SP, 160)  # Will cause fault

    fan.update()
    assert dm.read_di(Addresses.DI_FAN_FAULT) is True
    
    # Trigger alarm reset and update again
    dm.write_coil(Addresses.COIL_ALARM_RESET, True)
    fan.update()
    
    # Fault should be cleared
    assert dm.read_di(Addresses.DI_FAN_FAULT) is False


def test_random_jitter_in_rpm(monkeypatch):
    """Test that RPM includes random jitter"""
    # Mock random to return specific values
    monkeypatch.setattr(random, "randint", lambda a, b: 5)  # Always return +5
    
    dm = DataModel()
    fan = FanController(dm)
    
    dm.write_coil(Addresses.COIL_FAN_ENABLE, True)
    dm.write_holding(Addresses.HR_FAN_MODE_CMD, 1)
    dm.write_holding(Addresses.HR_FAN_RPM_SP, 500)

    fan.update()
    
    # Should be 500 * 0.6 + 5 = 305
    assert dm.read_input(Addresses.IR_FAN_RPM) == 305