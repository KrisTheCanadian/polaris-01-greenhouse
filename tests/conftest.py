import pytest
import random
from pyModbusTCP.server import DataBank

from server.data_model import DataModel
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


@pytest.fixture
def data_model():
    """Create a fresh DataModel instance for each test"""
    return DataModel()


@pytest.fixture
def fan_controller(data_model):
    """Create a FanController with the fixture data_model"""
    return FanController(data_model)


@pytest.fixture
def sensor_simulator(data_model, fan_controller):
    """Create a SensorSimulator with the fixture data_model and fan_controller"""
    return SensorSimulator(data_model, fan_controller)


@pytest.fixture
def controlled_system(data_model, fan_controller, sensor_simulator, mock_random):
    """Create a complete system with deterministic random"""
    mock_random()
    return {
        'data_model': data_model,
        'fan': fan_controller,
        'sensors': sensor_simulator
    }