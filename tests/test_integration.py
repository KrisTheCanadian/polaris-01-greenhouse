import pytest
from unittest.mock import patch

from server.data_model import Addresses


def test_complete_system_off_state(controlled_system):
    """Test system behavior when fan is off"""
    system = controlled_system
    dm = system['data_model']
    
    # Set fan to off
    dm.write_coil(Addresses.COIL_FAN_ENABLE, False)
    
    # Run one update cycle
    system['fan'].update()
    system['sensors'].update()
    
    # Verify expected values
    assert dm.read_input(Addresses.IR_FAN_STATE) == 0
    assert dm.read_input(Addresses.IR_FAN_RPM) == 0
    assert dm.read_input(Addresses.IR_AIRFLOW) == 0
    assert dm.read_di(Addresses.DI_FAN_RUNNING) is False
    assert dm.read_di(Addresses.DI_FAN_FAULT) is False


def test_complete_system_low_state(controlled_system):
    """Test system behavior when fan is on low"""
    system = controlled_system
    dm = system['data_model']
    
    # Set fan to low
    dm.write_coil(Addresses.COIL_FAN_ENABLE, True)
    dm.write_holding(Addresses.HR_FAN_MODE_CMD, 1)
    
    # Run one update cycle
    system['fan'].update()
    system['sensors'].update()
    
    # Verify expected values
    assert dm.read_input(Addresses.IR_FAN_STATE) == 1
    assert dm.read_input(Addresses.IR_FAN_RPM) > 0
    assert dm.read_input(Addresses.IR_AIRFLOW) == 200
    assert dm.read_di(Addresses.DI_FAN_RUNNING) is True
    assert dm.read_di(Addresses.DI_FAN_FAULT) is False
    
    # Temperature should be lower than base when fan is running
    assert dm.read_input(Addresses.IR_TEMPERATURE) < 225


def test_complete_system_high_state(controlled_system):
    """Test system behavior when fan is on high"""
    system = controlled_system
    dm = system['data_model']
    
    # Set fan to high
    dm.write_coil(Addresses.COIL_FAN_ENABLE, True)
    dm.write_holding(Addresses.HR_FAN_MODE_CMD, 2)
    
    # Run one update cycle
    system['fan'].update()
    system['sensors'].update()
    
    # Verify expected values
    assert dm.read_input(Addresses.IR_FAN_STATE) == 2
    assert dm.read_input(Addresses.IR_FAN_RPM) > 0
    assert dm.read_input(Addresses.IR_AIRFLOW) == 350
    assert dm.read_di(Addresses.DI_FAN_RUNNING) is True
    assert dm.read_di(Addresses.DI_FAN_FAULT) is False
    
    # Temperature should be even lower than in low state
    assert dm.read_input(Addresses.IR_TEMPERATURE) < 220


def test_fault_condition_and_recovery(controlled_system):
    """Test that a fault can occur and be cleared"""
    system = controlled_system
    dm = system['data_model']
    
    # Create a fault condition: low RPM setpoint
    dm.write_coil(Addresses.COIL_FAN_ENABLE, True)
    dm.write_holding(Addresses.HR_FAN_MODE_CMD, 1)
    dm.write_holding(Addresses.HR_FAN_RPM_SP, 150)  # Will result in RPM < 100
    
    # Run one update cycle to create fault
    system['fan'].update()
    system['sensors'].update()
    
    # Verify fault detected
    assert dm.read_di(Addresses.DI_FAN_FAULT) is True
    
    # Clear fault via alarm reset
    dm.write_coil(Addresses.COIL_ALARM_RESET, True)
    
    # Run another update cycle
    system['fan'].update()
    
    # Verify fault cleared
    assert dm.read_di(Addresses.DI_FAN_FAULT) is False
    
    # Alarm reset should be consumed (auto-cleared)
    assert dm.read_coil(Addresses.COIL_ALARM_RESET) is False


def test_dirty_filter_condition(controlled_system):
    """Test that a dirty filter condition can be detected"""
    system = controlled_system
    dm = system['data_model']
    
    # Set fan running
    dm.write_coil(Addresses.COIL_FAN_ENABLE, True)
    dm.write_holding(Addresses.HR_FAN_MODE_CMD, 1)
    
    # Patch the random function to create low airflow
    with patch('random.randint', return_value=-150):  # Makes airflow < 100
        system['fan'].update()
        system['sensors'].update()
    
    # Verify dirty filter detected
    assert dm.read_di(Addresses.DI_FILTER_DIRTY) is True