import pytest
import random

from server.data_model import DataModel, Addresses
from server.fan import FanController
from server.sensors import SensorSimulator


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


def test_simulation_disabled():
    dm = DataModel()
    fan = FanController(dm)
    sensors = SensorSimulator(dm, fan)
    
    # Disable simulation
    dm.write_holding(Addresses.HR_SIM_ENABLE, 0)
    
    # Set initial values
    dm.set_temperature(200)
    dm.set_humidity(450)
    dm.set_airflow(150)
    
    # Update shouldn't change values when simulation is disabled
    sensors.update()
    
    assert dm.read_input(Addresses.IR_TEMPERATURE) == 200
    assert dm.read_input(Addresses.IR_HUMIDITY) == 450
    assert dm.read_input(Addresses.IR_AIRFLOW) == 150


def test_fan_off_simulation(mock_random):
    # Test values when fan is off
    # No random jitter (set to 0)
    mock_random([0, 0, 0])  # For temp, humidity, airflow
    
    dm = DataModel()
    fan = FanController(dm)
    sensors = SensorSimulator(dm, fan)
    
    # Enable simulation
    dm.write_holding(Addresses.HR_SIM_ENABLE, 1)
    # Set fan off
    dm.set_fan_state(0)
    
    sensors.update()
    
    # Temperature increases when fan is off (base + 30)
    assert dm.read_input(Addresses.IR_TEMPERATURE) == 255  # 225 + 30 + 0
    # Humidity around 50%
    assert dm.read_input(Addresses.IR_HUMIDITY) == 500  # 500 + 0
    # No airflow when fan is off
    assert dm.read_input(Addresses.IR_AIRFLOW) == 0
    # Filter not dirty when fan is off
    assert dm.read_di(Addresses.DI_FILTER_DIRTY) is False


def test_fan_low_simulation(mock_random):
    # Test values when fan is on low
    mock_random([0, 0, 0])  # For temp, humidity, airflow
    
    dm = DataModel()
    fan = FanController(dm)
    sensors = SensorSimulator(dm, fan)
    
    # Enable simulation
    dm.write_holding(Addresses.HR_SIM_ENABLE, 1)
    # Set fan low
    dm.set_fan_state(1)
    
    sensors.update()
    
    # Temperature decreases when fan is on (base - 5*state)
    assert dm.read_input(Addresses.IR_TEMPERATURE) == 220  # 225 - 5*1 + 0
    # Humidity around 50%
    assert dm.read_input(Addresses.IR_HUMIDITY) == 500  # 500 + 0
    # Airflow at low setting
    assert dm.read_input(Addresses.IR_AIRFLOW) == 200  # 200 + 0
    # Filter not dirty with normal airflow
    assert dm.read_di(Addresses.DI_FILTER_DIRTY) is False


def test_fan_high_simulation(mock_random):
    # Test values when fan is on high
    mock_random([0, 0, 0])  # For temp, humidity, airflow
    
    dm = DataModel()
    fan = FanController(dm)
    sensors = SensorSimulator(dm, fan)
    
    # Enable simulation
    dm.write_holding(Addresses.HR_SIM_ENABLE, 1)
    # Set fan high
    dm.set_fan_state(2)
    
    sensors.update()
    
    # Temperature decreases when fan is on (base - 5*state)
    assert dm.read_input(Addresses.IR_TEMPERATURE) == 215  # 225 - 5*2 + 0
    # Humidity around 50%
    assert dm.read_input(Addresses.IR_HUMIDITY) == 500  # 500 + 0
    # Airflow at high setting
    assert dm.read_input(Addresses.IR_AIRFLOW) == 350  # 350 + 0
    # Filter not dirty with normal airflow
    assert dm.read_di(Addresses.DI_FILTER_DIRTY) is False


def test_filter_dirty_detection(mock_random):
    # Test that low airflow with fan on triggers filter dirty
    mock_random([0, 0, -300])  # Last value makes airflow very low
    
    dm = DataModel()
    fan = FanController(dm)
    sensors = SensorSimulator(dm, fan)
    
    # Enable simulation
    dm.write_holding(Addresses.HR_SIM_ENABLE, 1)
    # Set fan on
    dm.set_fan_state(1)
    
    sensors.update()
    
    # Airflow should be low due to the -300 random adjustment
    assert dm.read_input(Addresses.IR_AIRFLOW) == 0  # max(0, 200 - 300)
    # Filter should be detected as dirty
    assert dm.read_di(Addresses.DI_FILTER_DIRTY) is True


def test_temperature_bounds(monkeypatch):
    # Test temperature stays within bounds
    
    # First test the upper bound
    monkeypatch.setattr(random, "randint", lambda a, b: 100)  # Large positive
    
    dm = DataModel()
    fan = FanController(dm)
    sensors = SensorSimulator(dm, fan)
    
    dm.write_holding(Addresses.HR_SIM_ENABLE, 1)
    dm.set_fan_state(0)  # Off to get highest temp
    
    sensors.update()
    
    # Should be capped at 300 (30.0°C)
    assert dm.read_input(Addresses.IR_TEMPERATURE) == 300
    
    # Then test the lower bound
    monkeypatch.setattr(random, "randint", lambda a, b: -100)  # Large negative
    
    dm.set_fan_state(2)  # High to get lowest temp
    
    sensors.update()
    
    # Should be capped at 150 (15.0°C)
    assert dm.read_input(Addresses.IR_TEMPERATURE) == 150