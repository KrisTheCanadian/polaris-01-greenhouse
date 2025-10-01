# Modbus Server Tests

This directory contains unit and integration tests for the Modbus server components.

## Test Structure

- `test_data_model.py` - Tests for the `DataModel` class that handles the Modbus register/coil access
- `test_fan_controller.py` - Tests for the `FanController` class that manages fan state and RPM
- `test_sensors.py` - Tests for the `SensorSimulator` class that provides simulated sensor values
- `test_server.py` - Tests for the server startup and configuration components
- `test_integration.py` - Integration tests for the complete system

## Running Tests

To run all tests:

```bash
python -m pytest -v
```

To run a specific test file:

```bash
python -m pytest -v tests/test_data_model.py
```

To run tests with coverage report:

```bash
python -m pytest --cov=server tests/
```

## Test Design

The tests use fixtures defined in `conftest.py` including:

- `data_model`: Creates a fresh `DataModel` instance
- `fan_controller`: Creates a `FanController` connected to the data model
- `sensor_simulator`: Creates a `SensorSimulator` connected to the data model and fan controller
- `mock_random`: Replaces Python's random functions with deterministic values for testing
- `controlled_system`: Creates a complete system with all components

## Mocking Strategy

Random values are mocked to ensure tests are deterministic and repeatable. The `MockRandom` class in `conftest.py` provides a way to specify sequences of "random" values for testing.

Network interactions with the Modbus server are mocked in `test_server.py` to avoid actual socket binding.