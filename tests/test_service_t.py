from unittest.mock import patch

import pytest

from services import ServiceT


def test_t_write_read_success(env):
    t_service = ServiceT(
        env, read_failure_probability=0.0, write_failure_probability=0.0
    )
    t_service.write(1, "data_1")
    val = t_service.read(1)
    assert val == "data_1"
    print("T: write/read success test passed")


def test_t_read_not_found(env):
    t_service = ServiceT(
        env, read_failure_probability=0.0, write_failure_probability=0.0
    )
    with pytest.raises(RuntimeError, match="data not found"):
        t_service.read(999)
    print("T: read not found test passed")


def test_t_read_error(env):
    t_service = ServiceT(
        env, read_failure_probability=1.0, write_failure_probability=0.0
    )
    with pytest.raises(RuntimeError, match="failed"):
        t_service.read(999)
    print("T: read error test passed")


def test_t_write_error(env):
    t_service = ServiceT(
        env, read_failure_probability=0.0, write_failure_probability=1.0
    )
    with pytest.raises(RuntimeError, match="failed"):
        t_service.write(1, "data")
    print("T: write error test passed")
