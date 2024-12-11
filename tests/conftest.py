# tests/conftest.py
import pytest
import simpy


@pytest.fixture
def env():
    return simpy.Environment()
