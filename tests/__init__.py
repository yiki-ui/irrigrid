# ============= tests/__init__.py =============
"""Test Suite Package"""

import pytest

# Test configuration
pytest_plugins = [
    "pytest_asyncio",
]

# Global test configuration
TEST_DB_URL = "sqlite:///./test_irrigation.db"

__all__ = [
    'pytest',
    'TEST_DB_URL'
]