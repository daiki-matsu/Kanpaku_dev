import pytest
import tempfile
import os
from pathlib import Path

@pytest.fixture
def temp_project_dir():
    """Temporary project directory for SafeIO tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def safe_io_instance(temp_project_dir):
    """SafeIO instance with temporary directory"""
    from src.executor.safe_io import SafeIO
    return SafeIO(base_project_dir=temp_project_dir)
