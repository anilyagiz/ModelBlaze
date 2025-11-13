"""
Tests for ModelBlaze Optimizer
"""

import pytest
from src.optimizer import ModelBlaze


def test_optimizer_init():
    """Test ModelBlaze initialization"""
    optimizer = ModelBlaze()
    assert optimizer is not None
    assert optimizer.loader is not None
    assert optimizer.quantizer is not None
    assert optimizer.pruner is not None
    assert optimizer.benchmarker is not None


def test_list_target_devices():
    """Test listing target devices"""
    optimizer = ModelBlaze()
    devices = optimizer.list_target_devices()

    assert len(devices) > 0
    assert "mobile" in devices
    assert "iphone" in devices
    assert "android" in devices


def test_get_device_config():
    """Test getting device configuration"""
    optimizer = ModelBlaze()

    mobile_config = optimizer.get_device_config("mobile")
    assert "optimization_level" in mobile_config

    iphone_config = optimizer.get_device_config("iphone")
    assert "format" in iphone_config
    assert iphone_config["format"] == "coreml"
